from __future__ import annotations

import json
import sys
from pathlib import Path


def read_message():
    line = sys.stdin.buffer.readline()
    if line == b"":
        return None
    return json.loads(line.decode("utf-8"))


def write_message(message):
    body = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(body + b"\n")
    sys.stdout.buffer.flush()


def tool_result_for(message):
    params = message.get("params", {})
    name = params.get("name")
    arguments = params.get("arguments", {})
    if name == "list_directory":
        path = Path(arguments["path"])
        return {"content": [{"type": "text", "text": "\n".join(sorted(p.name for p in path.iterdir()))}]}
    if name == "read_file":
        path = Path(arguments["path"])
        return {"content": [{"type": "text", "text": path.read_text(encoding="utf-8")}]}
    return {"isError": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}


while True:
    request = read_message()
    if request is None:
        break
    method = request.get("method")
    if method == "notifications/initialized":
        continue
    if method == "initialize":
        write_message(
            {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fake", "version": "0.1.0"},
                },
            }
        )
    elif method == "tools/list":
        write_message(
            {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": {
                    "tools": [
                        {
                            "name": "read_file",
                            "description": "Read a file",
                            "inputSchema": {"type": "object"},
                        },
                        {
                            "name": "list_directory",
                            "description": "List a directory",
                            "inputSchema": {"type": "object"},
                        },
                    ]
                },
            }
        )
    elif method == "tools/call":
        write_message(
            {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": tool_result_for(request),
            }
        )
