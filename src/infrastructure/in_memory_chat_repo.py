from datetime import datetime, timezone
from typing import Dict

from ..domain.chat import Chat
from ..domain.repositories.chat_repo import ChatRepo


class InMemoryChatRepo(ChatRepo):
    def __init__(self) -> None:
        self._chats: Dict[str, Chat] = {}

    def load_chat(self, chat_id: str, user_id: str | None = None) -> Chat:
        chat = self._chats.get(chat_id)
        if chat is not None:
            return chat
        return Chat(
            chat_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="active",
        )

    def save_chat(self, chat: Chat) -> None:
        self._chats[chat.id] = chat
