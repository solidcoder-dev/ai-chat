import shutil
from pathlib import Path

import pytest

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.assistant_response import AssistantResponse
from src.application.dtos.mcp_tool_descriptor import McpToolDescriptor
from src.application.ports.assistant import Assistant
from src.application.services.orchestrated_chat_engine import OrchestratedChatEngine
from src.composition.coding_wiring import (
    READ_ONLY_FILESYSTEM_TOOL_NAMES,
    build_coding_chat_engine,
    build_filesystem_mcp_tooling,
)
from src.domain.tool import ToolResult
from src.infrastructure.in_memory_chat_repo import InMemoryChatRepo
from src.infrastructure.mcp.mcp_server_config import McpServerConfig
from src.infrastructure.mcp.stdio_mcp_client import McpConnectionError, StdioMcpClient


class FakeAssistant(Assistant):
    def __init__(self) -> None:
        self.requests = []

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="filesystem.read_file",
                tool_args={"path": "README.md", "call_id": "read-1"},
            )
        tool_result = request.messages[-1].content.items[0].data
        text = tool_result.result["content"][0]["text"]
        return AssistantResponse(
            kind="message",
            content=f"The README says: {text}",
            tool_name="",
            tool_args={},
        )


class AlwaysToolCallingAssistant(Assistant):
    def infer(self, request: AssistantRequest) -> AssistantResponse:
        return AssistantResponse(
            kind="tool_call",
            content="",
            tool_name="filesystem.read_file",
            tool_args={"path": "README.md"},
        )


class FakeMcpClient:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    def list_tools(self):
        return [
            McpToolDescriptor(
                name="read_file",
                description="Read a file",
                parameters_schema={"type": "object"},
            ),
            McpToolDescriptor(
                name="write_file",
                description="Write a file",
                parameters_schema={"type": "object"},
            ),
        ]

    def call_tool(self, name, arguments):
        if name != "read_file":
            raise AssertionError(f"unexpected tool {name}")
        path = self.root_path / str(arguments["path"])
        return {"content": [{"type": "text", "text": path.read_text(encoding="utf-8")}]}

    def close(self):
        pass


def make_engine(tmp_path, assistant):
    tools = FakeMcpClient(tmp_path).list_tools()
    tooling = build_filesystem_mcp_tooling(
        workspace_path=tmp_path,
        client=FakeMcpClient(tmp_path),
        discovered_tools=tools,
    )
    return OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=assistant,
        tool_registry=tooling.registry,
        tool_catalog=tooling.catalog,
        tool_access_policy=tooling.tool_access_policy,
        max_tool_calls=3,
    )


def test_coding_chat_engine_executes_filesystem_read_tool(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    assistant = FakeAssistant()
    engine = make_engine(tmp_path, assistant)

    response = engine.handle_user_message("chat-1", "Read README", user_id="user-1")

    tool_result = assistant.requests[1].messages[-1].content.items[0].data
    assert isinstance(tool_result, ToolResult)
    assert "Hello from this project" in str(tool_result.result)
    assert response.content == "The README says: Hello from this project"


def test_coding_chat_engine_returns_final_answer_after_tool_result(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    engine = make_engine(tmp_path, FakeAssistant())

    response = engine.handle_user_message("chat-2", "Read README", user_id="user-1")

    assert "Hello from this project" in response.content


def test_coding_chat_engine_does_not_expose_write_tools(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    assistant = FakeAssistant()
    engine = make_engine(tmp_path, assistant)

    engine.handle_user_message("chat-3", "Read README", user_id="user-1")

    exposed_tool_names = {tool.name for tool in assistant.requests[0].tools}
    assert "filesystem.read_file" in exposed_tool_names
    assert "filesystem.write_file" not in exposed_tool_names


def test_coding_chat_engine_stops_at_tool_call_limit(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    engine = make_engine(tmp_path, AlwaysToolCallingAssistant())

    with pytest.raises(ValueError, match="Tool call limit exceeded"):
        engine.handle_user_message("chat-4", "Read README", user_id="user-1")


def test_coding_wiring_uses_read_only_filesystem_tools():
    assert "filesystem.read_file" in READ_ONLY_FILESYSTEM_TOOL_NAMES
    assert "filesystem.write_file" not in READ_ONLY_FILESYSTEM_TOOL_NAMES
    assert "filesystem.edit_file" not in READ_ONLY_FILESYSTEM_TOOL_NAMES
    assert "filesystem.move_file" not in READ_ONLY_FILESYSTEM_TOOL_NAMES
    assert "filesystem.create_directory" not in READ_ONLY_FILESYSTEM_TOOL_NAMES


def test_real_filesystem_mcp_read_file_flow_with_fake_assistant(tmp_path):
    if shutil.which("npx") is None:
        pytest.skip("npx is not installed")
    (tmp_path / "README.md").write_text("Hello from real MCP", encoding="utf-8")
    client = None
    try:
        client = StdioMcpClient(
            McpServerConfig.filesystem("filesystem", tmp_path),
            request_timeout_seconds=20,
        )
    except McpConnectionError as exc:
        pytest.skip(f"MCP filesystem server is unavailable: {exc}")

    try:
        engine = build_coding_chat_engine(
            workspace_path=tmp_path,
            assistant=FakeAssistant(),
            chat_repo=InMemoryChatRepo(),
            mcp_client=client,
        )
        response = engine.handle_user_message("chat-5", "Read README", user_id="user-1")
    finally:
        client.close()

    assert "Hello from real MCP" in response.content
