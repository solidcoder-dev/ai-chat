from typing import List

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.assistant_response import AssistantResponse
from src.application.dtos.tool_spec import ToolSpec
from src.application.ports.assistant import Assistant
from src.application.services.orchestrated_chat_engine import OrchestratedChatEngine
from src.infrastructure.in_memory_chat_repo import InMemoryChatRepo
from src.infrastructure.tool_access_policy import AllowAllToolAccessPolicy, AllowNamedToolsPolicy
from src.infrastructure.tool_catalog import InMemoryToolCatalog
from src.infrastructure.tool_registry import InMemoryToolRegistry


class StubAssistant(Assistant):
    def __init__(self, responses: List[AssistantResponse]) -> None:
        self._responses = responses
        self.requests: List[AssistantRequest] = []

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self.requests.append(request)
        return self._responses.pop(0)


class EchoTool:
    def __init__(self) -> None:
        self.calls = []

    def run(self, args):
        self.calls.append(args)
        return {"echo": args.get("input")}


class WriteTool:
    def __init__(self) -> None:
        self.executed = False

    def run(self, args):
        self.executed = True
        return {"written": True}


def test_chat_engine_message_response():
    assistant = StubAssistant(
        [
            AssistantResponse(
                kind="message",
                content="hello",
                tool_name="",
                tool_args={},
            )
        ]
    )
    engine = OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=assistant,
        tool_registry=InMemoryToolRegistry({}),
        tool_catalog=InMemoryToolCatalog([]),
        tool_access_policy=AllowAllToolAccessPolicy(),
    )

    response = engine.handle_user_message("chat-1", "hi", user_id="user-1")
    assert response.content == "hello"


def test_chat_engine_tool_call_flow():
    tool = EchoTool()
    assistant = StubAssistant(
        [
            AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="echo",
                tool_args={"input": "ping", "call_id": "call-1"},
            ),
            AssistantResponse(
                kind="message",
                content="pong",
                tool_name="",
                tool_args={},
            ),
        ]
    )
    engine = OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=assistant,
        tool_registry=InMemoryToolRegistry({"echo": tool}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="echo", description="Echo tool", parameters_schema={})]
        ),
        tool_access_policy=AllowAllToolAccessPolicy(),
    )

    response = engine.handle_user_message("chat-2", "ping", user_id="user-1")
    assert response.content == "pong"
    assert len(assistant.requests) == 2
    assert tool.calls == [{"input": "ping"}]


def test_tool_call_metadata_is_not_passed_to_tool_arguments():
    tool = EchoTool()
    assistant = StubAssistant(
        [
            AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="echo",
                tool_args={"input": "ping", "_call_id": "call-42"},
            ),
            AssistantResponse(
                kind="message",
                content="done",
                tool_name="",
                tool_args={},
            ),
        ]
    )
    engine = OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=assistant,
        tool_registry=InMemoryToolRegistry({"echo": tool}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="echo", description="Echo tool", parameters_schema={})]
        ),
        tool_access_policy=AllowAllToolAccessPolicy(),
    )

    engine.handle_user_message("chat-3", "ping", user_id="user-1")

    assert tool.calls == [{"input": "ping"}]


def test_tool_call_id_is_preserved_outside_tool_arguments():
    tool = EchoTool()
    repo = InMemoryChatRepo()
    assistant = StubAssistant(
        [
            AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="echo",
                tool_args={"input": "ping"},
                tool_call_id="call-77",
            ),
            AssistantResponse(
                kind="message",
                content="done",
                tool_name="",
                tool_args={},
            ),
        ]
    )
    engine = OrchestratedChatEngine(
        chat_repo=repo,
        assistant=assistant,
        tool_registry=InMemoryToolRegistry({"echo": tool}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="echo", description="Echo tool", parameters_schema={})]
        ),
        tool_access_policy=AllowAllToolAccessPolicy(),
    )

    engine.handle_user_message("chat-4", "ping", user_id="user-1")

    loaded = repo.load_chat("chat-4", user_id="user-1")
    assert loaded.get_messages()[1].content.items[0].data.call_id == "call-77"
    assert tool.calls == [{"input": "ping"}]


def test_engine_rejects_tool_call_not_allowed_by_policy():
    write_tool = WriteTool()

    class BlockingAwareAssistant(Assistant):
        def __init__(self) -> None:
            self.calls = 0

        def infer(self, request: AssistantRequest) -> AssistantResponse:
            self.calls += 1
            if self.calls == 1:
                return AssistantResponse(
                    kind="tool_call",
                    content="",
                    tool_name="filesystem.write_file",
                    tool_args={"path": "README.md", "content": "x", "call_id": "blocked-1"},
                )
            tool_result = request.messages[-1].content.items[0].data
            return AssistantResponse(
                kind="message",
                content=tool_result.error["message"],
                tool_name="",
                tool_args={},
            )

    engine = OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=BlockingAwareAssistant(),
        tool_registry=InMemoryToolRegistry({"filesystem.write_file": write_tool}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="filesystem.write_file", description="Write tool", parameters_schema={})]
        ),
        tool_access_policy=AllowNamedToolsPolicy(set()),
    )

    response = engine.handle_user_message("chat-5", "write", user_id="user-1")

    assert "not allowed" in response.content
    assert write_tool.executed is False


def test_engine_does_not_execute_blocked_tool_even_if_registry_contains_it():
    write_tool = WriteTool()
    assistant = StubAssistant(
        [
            AssistantResponse(
                kind="tool_call",
                content="",
                tool_name="filesystem.write_file",
                tool_args={"path": "README.md", "content": "x"},
            ),
            AssistantResponse(
                kind="message",
                content="blocked",
                tool_name="",
                tool_args={},
            ),
        ]
    )
    engine = OrchestratedChatEngine(
        chat_repo=InMemoryChatRepo(),
        assistant=assistant,
        tool_registry=InMemoryToolRegistry({"filesystem.write_file": write_tool}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="filesystem.write_file", description="Write tool", parameters_schema={})]
        ),
        tool_access_policy=AllowNamedToolsPolicy({"filesystem.read_file"}),
    )

    response = engine.handle_user_message("chat-6", "write", user_id="user-1")

    assert response.content == "blocked"
    assert write_tool.executed is False
