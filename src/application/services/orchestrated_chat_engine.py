from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Sequence

from ..dtos.assistant_request import AssistantRequest
from ..dtos.assistant_response import AssistantResponse
from ..dtos.chat_response import ChatResponse
from ..ports.assistant import Assistant
from ..ports.tool_access_policy import ToolAccessPolicy
from ..ports.tool_catalog import ToolCatalog
from ..ports.tool_registry import ToolRegistry
from .chat_engine import ChatEngine
from ...domain.chat import Chat
from ...domain.message import Content, Message, TextContent, TextMessage, ToolCallMessage, ToolResultMessage
from ...domain.repositories.chat_repo import ChatRepo
from ...domain.tool import ToolCall, ToolResult


class OrchestratedChatEngine(ChatEngine):
    def __init__(
        self,
        chat_repo: ChatRepo,
        assistant: Assistant,
        tool_registry: ToolRegistry,
        tool_catalog: ToolCatalog,
        tool_access_policy: ToolAccessPolicy,
        max_tool_calls: int = 3,
    ) -> None:
        self._chat_repo = chat_repo
        self._assistant = assistant
        self._tool_registry = tool_registry
        self._tool_catalog = tool_catalog
        self._tool_access_policy = tool_access_policy
        self._max_tool_calls = max_tool_calls

    def handle_user_message(self, chat_id: str, text: str) -> ChatResponse:
        chat = self._chat_repo.load_chat(chat_id)
        chat.add_message(self._make_text_message(role="user", text=text))

        response = self._run_assistant_loop(chat)
        if response.kind == "message":
            chat.add_message(self._make_text_message(role="assistant", text=response.content))

        self._chat_repo.save_chat(chat)
        return ChatResponse(chat_id=chat.id, content=response.content, meta={})

    def _run_assistant_loop(self, chat: Chat) -> AssistantResponse:
        tools = self._allowed_tools()
        request = AssistantRequest(messages=chat.get_messages(), tools=tools)
        response = self._assistant.infer(request)

        tool_calls = 0
        while response.kind == "tool_call":
            tool_calls += 1
            if tool_calls > self._max_tool_calls:
                raise ValueError("Tool call limit exceeded")

            call_id = response.tool_args.get("call_id", f"call-{tool_calls}")
            call = ToolCall(call_id=call_id, name=response.tool_name, args=response.tool_args)
            chat.add_message(self._make_tool_call_message(call))

            tool = self._tool_registry.get_tool(response.tool_name)
            tool_result = tool.run(response.tool_args)
            result = ToolResult(call_id=call_id, status="ok", result=tool_result)
            chat.add_message(self._make_tool_result_message(result))

            request = AssistantRequest(messages=chat.get_messages(), tools=tools)
            response = self._assistant.infer(request)

        return response

    def _allowed_tools(self) -> Sequence:
        all_specs = self._tool_catalog.list_all_tool_specs()
        return self._tool_access_policy.get_allowed_tools(
            assistant_id="assistant",
            context={},
            all_specs=all_specs,
        )

    def _make_text_message(self, role: Literal["user", "assistant", "system"], text: str) -> Message:
        return Message(
            type="message",
            role=role,
            created_at=self._now_iso(),
            content=Content(
                items=[
                    TextMessage(
                        type="text",
                        renderable=True,
                        data=TextContent(text=text),
                    )
                ]
            ),
            _meta=None,
        )

    def _make_tool_call_message(self, call: ToolCall) -> Message:
        return Message(
            type="message",
            role="assistant",
            created_at=self._now_iso(),
            content=Content(
                items=[
                    ToolCallMessage(
                        type="tool_call",
                        renderable=False,
                        data=call,
                    )
                ]
            ),
            _meta=None,
        )

    def _make_tool_result_message(self, result: ToolResult) -> Message:
        return Message(
            type="message",
            role="assistant",
            created_at=self._now_iso(),
            content=Content(
                items=[
                    ToolResultMessage(
                        type="tool_result",
                        renderable=False,
                        data=result,
                    )
                ]
            ),
            _meta=None,
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
