from __future__ import annotations

import json
import os
import subprocess
import threading
from queue import Empty, Queue
from typing import Any, Sequence

from ...application.dtos.mcp_tool_descriptor import McpToolDescriptor
from ...application.ports.mcp_client import McpClient
from ...domain.structured_data import StructuredMap, StructuredValue
from .mcp_server_config import McpServerConfig


class McpConnectionError(RuntimeError):
    pass


class McpProtocolError(RuntimeError):
    pass


class StdioMcpClient(McpClient):
    def __init__(
        self,
        config: McpServerConfig,
        request_timeout_seconds: float = 10,
    ) -> None:
        self._config = config
        self._request_timeout_seconds = request_timeout_seconds
        self._next_request_id = 0
        self._responses: dict[int, Queue[dict[str, Any]]] = {}
        self._stderr_lines: Queue[str] = Queue()
        self._lock = threading.Lock()
        self._closed = False
        self._process = self._start_process()
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()
        try:
            self._initialize_session()
        except Exception:
            self.close()
            raise

    def list_tools(self) -> Sequence[McpToolDescriptor]:
        result = self._request("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise McpProtocolError("MCP tools/list response did not include tools")
        return [self._to_tool_descriptor(tool) for tool in tools]

    def call_tool(self, name: str, arguments: StructuredMap) -> StructuredValue:
        return self._request("tools/call", {"name": name, "arguments": dict(arguments)})

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

    def _start_process(self) -> subprocess.Popen:
        environment = os.environ.copy()
        if self._config.env:
            environment.update(self._config.env)
        try:
            return subprocess.Popen(
                self._config.command_line(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
            )
        except OSError as exc:
            raise McpConnectionError(
                f"Failed to start MCP server '{self._config.name}': {exc}"
            ) from exc

    def _initialize_session(self) -> None:
        self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ai-chat", "version": "0.1.0"},
            },
        )
        self._notification("notifications/initialized", {})

    def _request(self, method: str, params: StructuredMap) -> StructuredMap:
        request_id = self._reserve_request_id()
        self._responses[request_id] = Queue(maxsize=1)
        self._write_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": dict(params),
            }
        )
        response = self._wait_for_response(request_id, method)
        self._responses.pop(request_id, None)
        if "error" in response:
            raise McpProtocolError(f"MCP request '{method}' failed: {response['error']}")
        result = response.get("result")
        if not isinstance(result, dict):
            raise McpProtocolError(f"MCP request '{method}' returned an invalid result")
        return result

    def _notification(self, method: str, params: StructuredMap) -> None:
        self._write_message(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": dict(params),
            }
        )

    def _reserve_request_id(self) -> int:
        with self._lock:
            self._next_request_id += 1
            return self._next_request_id

    def _write_message(self, message: dict[str, Any]) -> None:
        if self._process.poll() is not None:
            raise McpConnectionError(self._server_stopped_message())
        if self._process.stdin is None:
            raise McpConnectionError("MCP server stdin is unavailable")
        try:
            self._process.stdin.write(json.dumps(message).encode("utf-8") + b"\n")
            self._process.stdin.flush()
        except OSError as exc:
            raise McpConnectionError(f"Failed to write to MCP server: {exc}") from exc

    def _wait_for_response(self, request_id: int, method: str) -> dict[str, Any]:
        response_queue = self._responses[request_id]
        try:
            return response_queue.get(timeout=self._request_timeout_seconds)
        except Empty as exc:
            if self._process.poll() is not None:
                raise McpConnectionError(self._server_stopped_message()) from exc
            raise McpConnectionError(
                f"MCP request '{method}' timed out after {self._request_timeout_seconds:g} seconds"
            ) from exc

    def _read_stdout(self) -> None:
        if self._process.stdout is None:
            return
        for line in self._process.stdout:
            message = self._read_line_message(line)
            if message is None:
                continue
            request_id = message.get("id")
            if isinstance(request_id, int) and request_id in self._responses:
                self._responses[request_id].put(message)

    @staticmethod
    def _read_line_message(line: bytes) -> dict[str, Any] | None:
        stripped = line.strip()
        if not stripped:
            return None
        return json.loads(stripped.decode("utf-8"))

    def _read_stderr(self) -> None:
        if self._process.stderr is None:
            return
        for line in self._process.stderr:
            stripped = line.decode("utf-8", errors="replace").strip()
            if stripped:
                self._stderr_lines.put(stripped)

    def _server_stopped_message(self) -> str:
        stderr = self._collect_stderr()
        if stderr:
            return f"MCP server '{self._config.name}' stopped: {stderr}"
        return f"MCP server '{self._config.name}' stopped"

    def _collect_stderr(self) -> str:
        lines = []
        while True:
            try:
                lines.append(self._stderr_lines.get_nowait())
            except Empty:
                break
        return "\n".join(lines[-10:])

    @staticmethod
    def _to_tool_descriptor(tool: Any) -> McpToolDescriptor:
        if not isinstance(tool, dict):
            raise McpProtocolError("MCP tool descriptor was not an object")
        return McpToolDescriptor(
            name=str(tool["name"]),
            description=str(tool.get("description", "")),
            parameters_schema=tool.get("inputSchema", {}),
        )
