from __future__ import annotations

from typing import Any, Dict

import logging

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
            text = str(payload.get("text", ""))
            if not text:
                await websocket.send_json({"error": "text is required"})
                continue
            response = await run_in_threadpool(_engine.handle_user_message, chat_id, text)
            await websocket.send_json({"chat_id": response.chat_id, "content": response.content})
    except WebSocketDisconnect as exc:
        logging.info("WebSocket client disconnected: code=%s", getattr(exc, "code", None))
    except Exception:
        logging.exception("WebSocket handler crashed")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

