from __future__ import annotations

from typing import Iterable, List

import ollama

from ..application.dtos.assistant_request import AssistantRequest
from ..application.dtos.assistant_response import AssistantResponse
from ..application.errors import LlmProviderError, ModelNotAvailableError
from ..application.ports.assistant import Assistant
from ..domain.message import Message, TextMessage


class OllamaAssistant(Assistant):
    def __init__(self, model: str = "llama3") -> None:
        self._model = model

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        messages = self._build_messages(request.messages)
        try:
            response = ollama.chat(model=self._model, messages=messages)
        except ollama.ResponseError as exc:
            message = str(exc)
            status_code = getattr(exc, "status_code", None)
            if status_code == 404 and "model" in message.lower() and "not found" in message.lower():
                raise ModelNotAvailableError(self._model, message) from exc
            raise LlmProviderError("ollama", message, status_code) from exc
        content = response["message"]["content"]
        return AssistantResponse(
            kind="message",
            content=content,
            tool_name="",
            tool_args={},
        )

    def _build_messages(self, messages: Iterable[Message]) -> List[dict]:
        rendered = []
        for message in messages:
            rendered.append(
                {
                    "role": message.role,
                    "content": self._render_message_content(message),
                }
            )
        return rendered

    def _render_message_content(self, message: Message) -> str:
        parts = []
        for item in message.content.items:
            if isinstance(item, TextMessage):
                parts.append(item.data.text)
        return "\n".join(parts)
