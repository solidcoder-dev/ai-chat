from __future__ import annotations

from typing import Iterable, List, Sequence, Type

from ..dtos.assistant_request import AssistantRequest
from ..dtos.assistant_response import AssistantResponse
from ..ports.assistant import Assistant


class MultiAssistant(Assistant):
    def __init__(
        self,
        children: Iterable[Assistant],
        recoverable_exceptions: Sequence[Type[Exception]] = (Exception,),
    ) -> None:
        self._children: List[Assistant] = list(children)
        self._recoverable_exceptions = tuple(recoverable_exceptions)

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        if not self._children:
            raise ValueError("MultiAssistant has no children")

        last_error: Exception | None = None
        for child in self._children:
            try:
                return child.infer(request)
            except self._recoverable_exceptions as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error

        raise ValueError("MultiAssistant could not obtain a response")

    def add_assistant(self, child: Assistant) -> None:
        self._children.append(child)

    def remove_assistant(self, child: Assistant) -> None:
        self._children.remove(child)
