from pathlib import Path

import pytest

import main
from src.application.dtos.chat_response import ChatResponse
from src.application.errors import ToolCallingNotSupportedError
from src.composition.coding_wiring import DEFAULT_CODING_MODEL


class FakeEngine:
    def __init__(self) -> None:
        self.messages = []

    def handle_user_message(self, chat_id: str, text: str, user_id: str | None = None):
        self.messages.append((chat_id, text, user_id))
        return ChatResponse(chat_id=chat_id, content=f"reply to {text}", meta={})


class FakeCodingSession:
    def __init__(self, workspace_path: Path) -> None:
        self.workspace_path = workspace_path
        self.engine = FakeEngine()
        self.closed = False

    def close(self) -> None:
        self.closed = True


class InputScript:
    def __init__(self, values):
        self._values = list(values)

    def __call__(self, prompt: str = "") -> str:
        return self._values.pop(0)


def test_default_cli_behavior_still_uses_default_chat_engine():
    engine = FakeEngine()
    output = []

    exit_code = main.run_cli(
        [],
        input_func=InputScript(["hello", "exit"]),
        output_func=output.append,
        chat_engine_builder=lambda: engine,
        coding_session_builder=lambda workspace_path, model=None: pytest.fail(
            "coding mode should not start"
        ),
    )

    assert exit_code == 0
    assert engine.messages == [("cli", "hello", "cli-user")]
    assert "Chat CLI. Type 'exit' to quit." in output
    assert "reply to hello" in output


def test_coding_cli_mode_builds_coding_chat_engine(tmp_path):
    session = FakeCodingSession(tmp_path.resolve())
    output = []
    built_workspaces = []
    selected_models = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path)],
        input_func=InputScript(["exit"]),
        output_func=output.append,
        chat_engine_builder=lambda: pytest.fail("default mode should not start"),
        coding_session_builder=lambda workspace_path, model=None: (
            built_workspaces.append(workspace_path),
            selected_models.append(model),
            session,
        )[-1],
    )

    assert exit_code == 0
    assert built_workspaces == [tmp_path.resolve()]
    assert selected_models == [None]
    assert session.closed is True
    assert "Coding assistant started." in output
    assert f"Workspace: {tmp_path.resolve()}" in output


def test_coding_cli_mode_requires_workspace_path():
    with pytest.raises(SystemExit):
        main.parse_args(["--mode", "coding"])


def test_coding_cli_accepts_workspace_path_with_spaces(tmp_path):
    workspace = tmp_path / "project with spaces"
    workspace.mkdir()
    session = FakeCodingSession(workspace.resolve())
    output = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(workspace)],
        input_func=InputScript(["exit"]),
        output_func=output.append,
        chat_engine_builder=lambda: pytest.fail("default mode should not start"),
        coding_session_builder=lambda workspace_path, model=None: session,
    )

    assert exit_code == 0
    assert f"Workspace: {workspace.resolve()}" in output


def test_coding_cli_closes_mcp_resources_when_exiting(tmp_path):
    session = FakeCodingSession(tmp_path.resolve())

    main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path)],
        input_func=InputScript(["exit"]),
        output_func=lambda message: None,
        coding_session_builder=lambda workspace_path, model=None: session,
    )

    assert session.closed is True


def test_coding_cli_prefixes_assistant_response(tmp_path):
    session = FakeCodingSession(tmp_path.resolve())
    output = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path)],
        input_func=InputScript(["hello", "exit"]),
        output_func=output.append,
        coding_session_builder=lambda workspace_path, model=None: session,
    )

    assert exit_code == 0
    assert "Assistant: reply to hello" in output


def test_coding_cli_reports_startup_failure(tmp_path):
    output = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path)],
        input_func=InputScript(["exit"]),
        output_func=output.append,
        coding_session_builder=lambda workspace_path, model=None: (_ for _ in ()).throw(
            RuntimeError("MCP request 'initialize' timed out")
        ),
    )

    assert exit_code == 1
    assert "Failed to start coding assistant: MCP request 'initialize' timed out" in output


def test_coding_cli_uses_model_argument_when_provided(tmp_path):
    session = FakeCodingSession(tmp_path.resolve())
    selected_models = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path), "--model", "llama3.1:8b"],
        input_func=InputScript(["exit"]),
        output_func=lambda message: None,
        coding_session_builder=lambda workspace_path, model=None: (
            selected_models.append(model),
            session,
        )[-1],
    )

    assert exit_code == 0
    assert selected_models == ["llama3.1:8b"]


def test_coding_cli_reports_clear_error_when_model_does_not_support_tools(tmp_path):
    output = []

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path), "--model", "llama3:latest"],
        input_func=InputScript(["exit"]),
        output_func=output.append,
        coding_session_builder=lambda workspace_path, model=None: (_ for _ in ()).throw(
            ToolCallingNotSupportedError("llama3:latest")
        ),
    )

    assert exit_code == 1
    assert any("Selected model 'llama3:latest' does not support tool calling." in line for line in output)
    assert any("python3 main.py --mode coding --workspace . --model llama3.1:8b" in line for line in output)


def test_coding_cli_closes_session_on_keyboard_interrupt(tmp_path):
    session = FakeCodingSession(tmp_path.resolve())
    output = []

    def raise_keyboard_interrupt(prompt: str = "") -> str:
        raise KeyboardInterrupt

    exit_code = main.run_cli(
        ["--mode", "coding", "--workspace", str(tmp_path)],
        input_func=raise_keyboard_interrupt,
        output_func=output.append,
        coding_session_builder=lambda workspace_path, model=None: session,
    )

    assert exit_code == 130
    assert session.closed is True
    assert "Coding assistant stopped." in output


def test_coding_cli_uses_tool_capable_default_model():
    args = main.parse_args(["--mode", "coding", "--workspace", "."])

    assert args.model is None
    assert DEFAULT_CODING_MODEL == "llama3.1:8b"
