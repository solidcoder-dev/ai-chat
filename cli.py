import asyncio
import json
import sys

import websockets


async def _send_once(url: str, chat_id: str, text: str) -> str:
    payload = {"chat_id": chat_id, "text": text}
    async with websockets.connect(url, ping_interval=None, ping_timeout=None) as websocket:
        await websocket.send(json.dumps(payload))
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("event") == "done":
                return data.get("content", "")
            if data.get("event") == "error":
                return f"Error: {data.get('error', '')}"


async def chat_loop(url: str) -> None:
    chat_id = "cli"
    print("Connected. Type 'exit' to quit.")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        try:
            content = await _send_once(url, chat_id, user_input)
        except websockets.exceptions.ConnectionClosedError:
            content = await _send_once(url, chat_id, user_input)
        print(content)


def main() -> None:
    url = "ws://localhost:8000/ws"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    asyncio.run(chat_loop(url))


if __name__ == "__main__":
    main()
