from abc import ABC, abstractmethod

from ..dtos.chat_response import ChatResponse


class ChatEngine(ABC):
    @abstractmethod
    def handle_user_message(self, chat_id: str, text: str) -> ChatResponse:
        raise NotImplementedError
