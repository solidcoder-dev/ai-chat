from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

from ..composition.wiring import build_chat_engine


logging.basicConfig(level=logging.INFO)

app = FastAPI()
_engine = build_chat_engine()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload: Dict[str, Any] = await websocket.receive_json()
            chat_id = str(payload.get("chat_id", "ws"))
            user_id = str(payload.get("user_id", "ws-user"))
            text = str(payload.get("text", ""))
            if not text:
                await websocket.send_json({"error": "text is required"})
                continue
            queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def on_event(message) -> None:
                event = {"event": "message", "message": asdict(message)}
                loop.call_soon_threadsafe(queue.put_nowait, event)

            task = asyncio.create_task(
                run_in_threadpool(
                    _engine.handle_user_message_with_events,
                    chat_id,
                    text,
                    on_event,
                    user_id,
                )
            )

            while True:
                if task.done() and queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    continue

            while not queue.empty():
                await websocket.send_json(queue.get_nowait())

            try:
                response = task.result()
            except Exception as exc:
                logging.exception("WebSocket handler crashed")
                await websocket.send_json({"event": "error", "error": str(exc)})
            else:
                await websocket.send_json(
                    {"event": "done", "chat_id": response.chat_id, "content": response.content}
                )
    except WebSocketDisconnect as exc:
        logging.info("WebSocket client disconnected: code=%s", getattr(exc, "code", None))
    except Exception:
        logging.exception("WebSocket handler crashed")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
