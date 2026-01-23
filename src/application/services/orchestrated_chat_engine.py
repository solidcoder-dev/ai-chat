from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Literal, Optional, Sequence
from uuid import uuid4

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
        agent_id: str = "assistant",
        agent_version: str = "1.0.0",
        system_prompt_id: str = "prompt-default",
    ) -> None:
        self._chat_repo = chat_repo
        self._assistant = assistant
        self._tool_registry = tool_registry
        self._tool_catalog = tool_catalog
        self._tool_access_policy = tool_access_policy
        self._max_tool_calls = max_tool_calls
        self._agent_id = agent_id
        self._agent_version = agent_version
        self._system_prompt_id = system_prompt_id

    def handle_user_message(self, chat_id: str, text: str, user_id: str | None = None) -> ChatResponse:
        chat = self._ensure_chat_metadata(
            self._chat_repo.load_chat(chat_id, user_id=user_id),
            user_id=user_id,
        )
        chat.add_message(self._make_text_message(role="user", text=text))

        response = self._run_assistant_loop(chat)
        if response.kind == "message":
            chat.add_message(self._make_text_message(role="assistant", text=response.content))

        self._chat_repo.save_chat(chat)
        return ChatResponse(chat_id=chat.id, content=response.content, meta={})

    def handle_user_message_with_events(
        self,
        chat_id: str,
        text: str,
        on_event: Optional[Callable[[Message], None]] = None,
        user_id: str | None = None,
    ) -> ChatResponse:
        chat = self._ensure_chat_metadata(
            self._chat_repo.load_chat(chat_id, user_id=user_id),
            user_id=user_id,
        )
        user_message = self._make_text_message(role="user", text=text)
        chat.add_message(user_message)
        self._emit(on_event, user_message)

        response = self._run_assistant_loop(chat, on_event=on_event)
        if response.kind == "message":
            assistant_message = self._make_text_message(role="assistant", text=response.content)
            chat.add_message(assistant_message)
            self._emit(on_event, assistant_message)

        self._chat_repo.save_chat(chat)
        return ChatResponse(chat_id=chat.id, content=response.content, meta={})

    def _run_assistant_loop(
        self,
        chat: Chat,
        *,
        on_event: Optional[Callable[[Message], None]] = None,
    ) -> AssistantResponse:
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
            tool_call_message = self._make_tool_call_message(call)
            chat.add_message(tool_call_message)
            self._emit(on_event, tool_call_message)

            tool = self._tool_registry.get_tool(response.tool_name)
            tool_result = tool.run(response.tool_args)
            result = ToolResult(call_id=call_id, status="ok", result=tool_result)
            tool_result_message = self._make_tool_result_message(result)
            chat.add_message(tool_result_message)
            self._emit(on_event, tool_result_message)

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
            message_id=self._new_message_id(),
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
            message_id=self._new_message_id(),
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
            message_id=self._new_message_id(),
            _meta=None,
        )

    def _ensure_chat_metadata(self, chat: Chat, *, user_id: str | None) -> Chat:
        if chat.user_id is not None:
            return chat
        if user_id is None:
            raise ValueError("user_id is required for new chats")
        return Chat(
            chat.id,
            user_id=user_id,
            agent_id=self._agent_id,
            agent_version=self._agent_version,
            system_prompt_id=self._system_prompt_id,
        )

    @staticmethod
    def _emit(on_event: Optional[Callable[[Message], None]], message: Message) -> None:
        if on_event is None:
            return
        on_event(message)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_message_id() -> str:
        return str(uuid4())
