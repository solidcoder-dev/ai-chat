from typing import List, Sequence

from .message import Message


class Chat:
    def __init__(self, chat_id: str) -> None:
        self._id = chat_id
        self._messages: List[Message] = []

    @property
    def id(self) -> str:
        return self._id

    def add_message(self, message: Message) -> None:
        self._messages.append(message)

    def get_messages(self) -> Sequence[Message]:
        return tuple(self._messages)
