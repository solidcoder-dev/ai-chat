from abc import ABC, abstractmethod

from ..chat import Chat


class ChatRepo(ABC):
    @abstractmethod
    def load_chat(self, chat_id: str) -> Chat:
        raise NotImplementedError

    @abstractmethod
    def save_chat(self, chat: Chat) -> None:
        raise NotImplementedError
