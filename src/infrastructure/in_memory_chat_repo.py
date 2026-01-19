from typing import Dict

from ..domain.chat import Chat
from ..domain.repositories.chat_repo import ChatRepo


class InMemoryChatRepo(ChatRepo):
    def __init__(self) -> None:
        self._chats: Dict[str, Chat] = {}

    def load_chat(self, chat_id: str) -> Chat:
        return self._chats.get(chat_id, Chat(chat_id))

    def save_chat(self, chat: Chat) -> None:
        self._chats[chat.id] = chat
