import asyncio
import json
import sys

import websockets


async def chat_loop(url: str) -> None:
    async with websockets.connect(url) as websocket:
        print("Connected. Type 'exit' to quit.")
        while True:
            user_input = input("> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            if not user_input:
                continue
            payload = {"chat_id": "cli", "text": user_input}
            await websocket.send(json.dumps(payload))
            response = await websocket.recv()
            data = json.loads(response)
            print(data.get("content", ""))


def main() -> None:
    url = "ws://localhost:8000/ws"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    asyncio.run(chat_loop(url))


if __name__ == "__main__":
    main()
