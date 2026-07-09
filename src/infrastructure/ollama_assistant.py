from __future__ import annotations

import json
import os
from typing import Callable, Iterable, List, Optional

import ollama

from ..application.dtos.assistant_request import AssistantRequest
from ..application.dtos.assistant_response import AssistantResponse
from ..application.dtos.tool_spec import ToolSpec
from ..application.errors import (
    LlmProviderError,
    ModelNotAvailableError,
    ToolCallingNotSupportedError,
)
from ..application.ports.assistant import Assistant
from ..domain.message import (
    Content,
    Message,
    TextContent,
    TextMessage,
    ToolCallMessage,
    ToolResultMessage,
)
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
        model: str,
        host: Optional[str] = None,
        client_factory: Optional[Callable[[Optional[str]], ollama.Client]] = None,
    ) -> None:
        self._model = model
        factory = client_factory or _default_client_factory
        self._client = factory(host)

    @property
    def model(self) -> str:
        return self._model

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        tool_mapper = OllamaToolMapper(request.tools)
        messages = self._build_messages(request.messages, tool_mapper)
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                tools=tool_mapper.to_ollama_tools(),
            )
        except ollama.ResponseError as exc:
            message = str(exc)
            status_code = getattr(exc, "status_code", None)
            if self._is_tool_support_error(message, status_code):
                raise ToolCallingNotSupportedError(self._model) from exc
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
                tool_call_id=self._tool_call_id(tool_call),
            )

        content = response["message"]["content"]
        if self._is_empty_message(content) and self._contains_tool_round_trip(request.messages):
            raise LlmProviderError(
                "ollama",
                "empty assistant response after tool execution",
            )
        return AssistantResponse(
            kind="message",
            content=content,
            tool_name="",
            tool_args={},
        )

    def assert_tool_calling_supported(self) -> None:
        self.infer(
            AssistantRequest(
                messages=[
                    Message(
                        type="message",
                        role="user",
                        created_at="1970-01-01T00:00:00Z",
                        content=Content(
                            items=[
                                TextMessage(
                                    type="text",
                                    renderable=True,
                                    data=TextContent(text="Confirm tool support."),
                                )
                            ]
                        ),
                        _meta=None,
                    )
                ],
                tools=[
                    ToolSpec(
                        name="tool_support_probe",
                        description="Checks whether the model accepts tool definitions.",
                        parameters_schema={
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    )
                ],
            )
        )

    def _build_messages(
        self,
        messages: Iterable[Message],
        tool_mapper: OllamaToolMapper,
    ) -> List[dict]:
        rendered = []
        tool_names_by_call_id: dict[str, str] = {}
        for message in messages:
            rendered.extend(
                self._render_message_parts(
                    message,
                    tool_mapper=tool_mapper,
                    tool_names_by_call_id=tool_names_by_call_id,
                )
            )
        return rendered

    def _render_message_parts(
        self,
        message: Message,
        *,
        tool_mapper: OllamaToolMapper,
        tool_names_by_call_id: dict[str, str],
    ) -> List[dict]:
        parts: List[dict] = []
        for item in message.content.items:
            if isinstance(item, TextMessage):
                parts.append(
                    {
                        "role": message.role,
                        "content": item.data.text,
                    }
                )
            if isinstance(item, ToolCallMessage):
                provider_name = tool_mapper.to_provider_name(item.data.name)
                tool_names_by_call_id[item.data.call_id] = provider_name
                parts.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": provider_name,
                                    "arguments": item.data.args,
                                }
                            }
                        ],
                    }
                )
            if isinstance(item, ToolResultMessage):
                tool_name = tool_names_by_call_id.get(item.data.call_id)
                parts.append(
                    {
                        "role": "tool",
                        "content": self._render_tool_result(item.data),
                        "tool_name": tool_name,
                    }
                )
        return parts

    @staticmethod
    def _render_tool_result(tool_result) -> str:
        if tool_result.status == "error":
            return json.dumps({"error": tool_result.error or {}})
        return json.dumps(tool_result.result)

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

    @staticmethod
    def _tool_call_id(tool_call: dict) -> str | None:
        call_id = tool_call.get("id")
        if isinstance(call_id, str) and call_id:
            return call_id
        return None

    @staticmethod
    def _is_tool_support_error(message: str, status_code: int | None) -> bool:
        return status_code == 400 and "does not support tools" in message.lower()

    @staticmethod
    def _is_empty_message(content: str | None) -> bool:
        return content is None or content.strip() == ""

    @staticmethod
    def _contains_tool_round_trip(messages: Iterable[Message]) -> bool:
        for message in messages:
            for item in message.content.items:
                if isinstance(item, ToolResultMessage):
                    return True
        return False
