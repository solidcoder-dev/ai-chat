from __future__ import annotations

from ..dtos.assistant_request import AssistantRequest
from ..dtos.assistant_response import AssistantResponse
from ..ports.assistant import Assistant
from ..ports.logger import Logger


class LoggingAssistant(Assistant):
    def __init__(self, inner: Assistant, logger: Logger) -> None:
        self._inner = inner
        self._logger = logger

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self._logger.info(
            f"assistant.infer start messages={len(request.messages)} tools={len(request.tools)}"
        )
        try:
            response = self._inner.infer(request)
        except Exception as exc:
            self._logger.error(f"assistant.infer error={exc}")
            raise
        self._logger.info(f"assistant.infer done kind={response.kind}")
        return response
