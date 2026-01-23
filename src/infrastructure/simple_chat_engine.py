from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from ..application.dtos.assistant_request import AssistantRequest
from ..application.dtos.chat_response import ChatResponse
from ..application.services.chat_engine import ChatEngine
from ..domain.chat import Chat
from ..domain.message import Content, Message, TextContent, TextMessage
from ..domain.repositories.chat_repo import ChatRepo
from ..application.ports.assistant import Assistant


class SimpleChatEngine(ChatEngine):
    def __init__(self, chat_repo: ChatRepo, assistant: Assistant) -> None:
        self._chat_repo = chat_repo
        self._assistant = assistant

    def handle_user_message(self, chat_id: str, text: str, user_id: str | None = None) -> ChatResponse:
        chat = self._chat_repo.load_chat(chat_id, user_id=user_id)
        chat.add_message(self._make_message(role="user", text=text))

        request = AssistantRequest(messages=chat.get_messages(), tools=[])
        assistant_response = self._assistant.infer(request)

        if assistant_response.kind == "message":
            chat.add_message(
                self._make_message(role="assistant", text=assistant_response.content)
            )

        self._chat_repo.save_chat(chat)

        return ChatResponse(
            chat_id=chat.id,
            content=assistant_response.content,
            meta={},
        )

    def _make_message(self, role: Literal["user", "assistant", "system"], text: str) -> Message:
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

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
