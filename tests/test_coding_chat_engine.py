import shutil
from pathlib import Path

import pytest

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.assistant_response import AssistantResponse
from src.application.dtos.mcp_tool_descriptor import McpToolDescriptor
from src.application.ports.assistant import Assistant
from src.application.services.orchestrated_chat_engine import OrchestratedChatEngine
from src.composition.coding_wiring import (
    DEFAULT_CODING_MODEL,
    SAFE_CODING_TOOL_NAMES,
    build_coding_chat_engine,
    build_coding_chat_session,
    build_filesystem_mcp_tooling,
    resolve_coding_model,
)
from src.domain.tool import ToolResult
from src.infrastructure.in_memory_chat_repo import InMemoryChatRepo
from src.infrastructure.mcp.mcp_server_config import McpServerConfig
from src.infrastructure.mcp.stdio_mcp_client import McpConnectionError, StdioMcpClient
from src.infrastructure.ollama_assistant import OllamaAssistant


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
        self.closed = False

    def list_tools(self):
        return [
            McpToolDescriptor(
                name="read_file",
                description="Read a file",
                parameters_schema={"type": "object"},
            ),
            McpToolDescriptor(
                name="list_directory",
                description="List a directory",
                parameters_schema={"type": "object"},
            ),
            McpToolDescriptor(
                name="write_file",
                description="Write a file",
                parameters_schema={"type": "object"},
            ),
        ]

    def call_tool(self, name, arguments):
        if name == "read_file":
            path = self.root_path / str(arguments["path"])
            return {"content": [{"type": "text", "text": path.read_text(encoding="utf-8")}]}
        if name == "list_directory":
            path = (self.root_path / str(arguments["path"])).resolve()
            return {
                "entries": [
                    {"name": child.name, "type": "directory" if child.is_dir() else "file"}
                    for child in sorted(path.iterdir())
                ]
            }
        raise AssertionError(f"unexpected tool {name}")

    def close(self):
        self.closed = True


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


class ProposeEditAssistant(Assistant):
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
        if len(self.requests) == 2:
            return AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="filesystem.propose_edit",
                tool_args={
                    "path": "README.md",
                    "new_content": "# AI Chat Coding Assistant\n",
                    "call_id": "proposal-1",
                },
            )
        diff = self.requests[-1].messages[-1].content.items[0].data.result["unified_diff"]
        return AssistantResponse(
            kind="message",
            content=f"I propose this change:\n\n```diff\n{diff}```\n\nNo files were modified.",
            tool_name="",
            tool_args={},
        )


class ListWorkspaceAssistant(Assistant):
    def __init__(self) -> None:
        self.requests = []

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="filesystem.list_directory",
                tool_args={"path": "."},
            )
        entries = self.requests[-1].messages[-1].content.items[0].data.result["entries"]
        names = ", ".join(entry["name"] for entry in entries)
        return AssistantResponse(
            kind="message",
            content=f"Workspace files: {names}",
            tool_name="",
            tool_args={},
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


def test_coding_chat_can_read_readme_with_fake_assistant(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    engine = make_engine(tmp_path, FakeAssistant())

    response = engine.handle_user_message("chat-readme", "Read README", user_id="user-1")

    assert "Hello from this project" in response.content


def test_coding_chat_engine_returns_final_answer_after_tool_result(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    engine = make_engine(tmp_path, FakeAssistant())

    response = engine.handle_user_message("chat-2", "Read README", user_id="user-1")

    assert "Hello from this project" in response.content


def test_coding_chat_can_list_workspace_files_with_fake_assistant(tmp_path):
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    (tmp_path / "src.py").write_text("print('x')", encoding="utf-8")
    engine = make_engine(tmp_path, ListWorkspaceAssistant())

    response = engine.handle_user_message("chat-list", "List files", user_id="user-1")

    assert "README.md" in response.content
    assert "src.py" in response.content


def test_coding_chat_engine_does_not_expose_write_tools(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    assistant = FakeAssistant()
    engine = make_engine(tmp_path, assistant)

    engine.handle_user_message("chat-3", "Read README", user_id="user-1")

    exposed_tool_names = {tool.name for tool in assistant.requests[0].tools}
    assert "filesystem.read_file" in exposed_tool_names
    assert "filesystem.propose_edit" in exposed_tool_names
    assert "filesystem.write_file" not in exposed_tool_names


def test_coding_chat_engine_stops_at_tool_call_limit(tmp_path):
    (tmp_path / "README.md").write_text("Hello from this project", encoding="utf-8")
    engine = make_engine(tmp_path, AlwaysToolCallingAssistant())

    with pytest.raises(ValueError, match="Tool call limit exceeded"):
        engine.handle_user_message("chat-4", "Read README", user_id="user-1")


def test_coding_policy_does_not_expose_write_edit_move_or_create_tools():
    assert "filesystem.read_file" in SAFE_CODING_TOOL_NAMES
    assert "filesystem.propose_edit" in SAFE_CODING_TOOL_NAMES
    assert "filesystem.write_file" not in SAFE_CODING_TOOL_NAMES
    assert "filesystem.edit_file" not in SAFE_CODING_TOOL_NAMES
    assert "filesystem.move_file" not in SAFE_CODING_TOOL_NAMES
    assert "filesystem.create_directory" not in SAFE_CODING_TOOL_NAMES


def test_coding_chat_engine_can_propose_edit_without_modifying_file(tmp_path):
    readme = tmp_path / "README.md"
    original = "# AI Chat\n"
    readme.write_text(original, encoding="utf-8")
    engine = make_engine(tmp_path, ProposeEditAssistant())

    response = engine.handle_user_message("chat-proposal", "Change title", user_id="user-1")

    assert "-# AI Chat" in response.content
    assert "+# AI Chat Coding Assistant" in response.content
    assert "No files were modified." in response.content
    assert readme.read_text(encoding="utf-8") == original


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


def test_coding_cli_uses_ollama_model_env_as_fallback(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:70b")

    assert resolve_coding_model(None) == "llama3.1:70b"


def test_coding_cli_uses_tool_capable_default_model(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    assert resolve_coding_model(None) == DEFAULT_CODING_MODEL


def test_ollama_assistant_receives_configured_model(tmp_path, monkeypatch):
    created_models = []

    class RecordingAssistant:
        def __init__(self, model: str) -> None:
            created_models.append(model)

    monkeypatch.setattr(
        "src.composition.coding_wiring.OllamaAssistant",
        RecordingAssistant,
    )

    build_coding_chat_engine(
        tmp_path,
        model="llama3.1:8b",
        mcp_client=FakeMcpClient(tmp_path),
    )

    assert created_models == ["llama3.1:8b"]


def test_coding_cli_closes_session_when_startup_fails_after_mcp_start(tmp_path):
    class FailingOllamaAssistant(OllamaAssistant):
        def assert_tool_calling_supported(self) -> None:
            raise RuntimeError("tool preflight failed")

    client = FakeMcpClient(tmp_path)

    with pytest.raises(RuntimeError, match="tool preflight failed"):
        build_coding_chat_session(
            workspace_path=tmp_path,
            assistant=FailingOllamaAssistant(
                model="llama3.1:8b",
                client_factory=lambda host: None,
            ),
            mcp_client=client,
        )

    assert client.closed is True
