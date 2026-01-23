from typing import List

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.assistant_response import AssistantResponse
from src.application.dtos.tool_spec import ToolSpec
from src.application.ports.assistant import Assistant
from src.application.services.orchestrated_chat_engine import OrchestratedChatEngine
from src.infrastructure.in_memory_chat_repo import InMemoryChatRepo
from src.infrastructure.tool_access_policy import AllowAllToolAccessPolicy
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
    def run(self, args):
        return {"echo": args.get("input")}


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
        tool_registry=InMemoryToolRegistry({"echo": EchoTool()}),
        tool_catalog=InMemoryToolCatalog(
            [ToolSpec(name="echo", description="Echo tool", parameters_schema={})]
        ),
        tool_access_policy=AllowAllToolAccessPolicy(),
    )

    response = engine.handle_user_message("chat-2", "ping", user_id="user-1")
    assert response.content == "pong"
    assert len(assistant.requests) == 2
