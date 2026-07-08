from __future__ import annotations

import json
import os
from typing import Callable, Iterable, List, Optional

import ollama

from ..application.dtos.assistant_request import AssistantRequest
from ..application.dtos.assistant_response import AssistantResponse
from ..application.errors import LlmProviderError, ModelNotAvailableError
from ..application.ports.assistant import Assistant
from ..domain.message import Message, TextMessage, ToolResultMessage
from .ollama_tool_mapper import OllamaToolMapper


def _resolve_host(host: Optional[str]) -> str:
    resolved = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not resolved.startswith(("http://", "https://")):
        resolved = f"http://{resolved}"
    return resolved


def _default_client_factory(host: Optional[str]) -> ollama.Client:
    return ollama.Client(host=_resolve_host(host))


class OllamaAssistant(Assistant):
    def __init__(
        self,
        model: str = "llama3",
        host: Optional[str] = None,
        client_factory: Optional[Callable[[Optional[str]], ollama.Client]] = None,
    ) -> None:
        self._model = model
        factory = client_factory or _default_client_factory
        self._client = factory(host)

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        messages = self._build_messages(request.messages)
        tool_mapper = OllamaToolMapper(request.tools)
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                tools=tool_mapper.to_ollama_tools(),
            )
        except ollama.ResponseError as exc:
            message = str(exc)
            status_code = getattr(exc, "status_code", None)
            if status_code == 404 and "model" in message.lower() and "not found" in message.lower():
                raise ModelNotAvailableError(self._model, message) from exc
            raise LlmProviderError("ollama", message, status_code) from exc
        except Exception as exc:
            raise LlmProviderError("ollama", str(exc)) from exc
        tool_call = self._first_tool_call(response)
        if tool_call is not None:
            function = tool_call["function"]
            return AssistantResponse(
                kind="tool_call",
                content="",
                tool_name=tool_mapper.to_internal_name(function["name"]),
                tool_args=self._tool_arguments(function.get("arguments", {})),
            )

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
            if isinstance(item, ToolResultMessage):
                parts.append(json.dumps({"tool_result": item.data.result}))
        return "\n".join(parts)

    @staticmethod
    def _first_tool_call(response) -> dict | None:
        tool_calls = response.get("message", {}).get("tool_calls") or []
        if not tool_calls:
            return None
        return tool_calls[0]

    @staticmethod
    def _tool_arguments(arguments) -> dict:
        if isinstance(arguments, str):
            return json.loads(arguments)
        return arguments
