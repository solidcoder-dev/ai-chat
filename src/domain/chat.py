from typing import List, Sequence

from .message import Message


class Chat:
    def __init__(
        self,
        chat_id: str,
        *,
        user_id: str | None = None,
        agent_id: str | None = None,
        agent_version: str | None = None,
        system_prompt_id: str | None = None,
    ) -> None:
        self._id = chat_id
        self._user_id = user_id
        self._agent_id = agent_id
        self._agent_version = agent_version
        self._system_prompt_id = system_prompt_id
        self._messages: List[Message] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def agent_id(self) -> str | None:
        return self._agent_id

    @property
    def agent_version(self) -> str | None:
        return self._agent_version

    @property
    def system_prompt_id(self) -> str | None:
        return self._system_prompt_id

    def add_message(self, message: Message) -> None:
        self._messages.append(message)

    def get_messages(self) -> Sequence[Message]:
        return tuple(self._messages)
