import pytest
import ollama

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.tool_spec import ToolSpec
from src.application.errors import ModelNotAvailableError, ToolCallingNotSupportedError
from src.domain.message import Content, Message, TextContent, TextMessage, ToolCallMessage
from src.domain.message import ToolResultMessage
from src.domain.tool import ToolCall, ToolResult
from src.infrastructure.ollama_assistant import OllamaAssistant


class FakeOllamaClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class RaisingOllamaClient:
    def __init__(self, exception):
        self._exception = exception

    def chat(self, **kwargs):
        raise self._exception


def _make_request() -> AssistantRequest:
    return AssistantRequest(
        messages=[
            Message(
                type="message",
                role="user",
                created_at="2020-01-01T00:00:00Z",
                content=Content(
                    items=[
                        TextMessage(
                            type="text",
                            renderable=True,
                            data=TextContent(text="Hello"),
                        )
                    ]
                ),
                _meta=None,
            )
        ],
        tools=[],
    )


def test_ollama_chat_response(ollama_ready) -> None:
    assistant = OllamaAssistant(model=ollama_ready["model"])
    response = assistant.infer(_make_request())
    assert response.kind == "message"
    assert response.content


def test_ollama_missing_model_raises_model_not_available(ollama_ready) -> None:
    assistant = OllamaAssistant(model="missing-model-for-test")
    with pytest.raises(ModelNotAvailableError):
        assistant.infer(_make_request())


def test_ollama_assistant_passes_tools_to_ollama_client():
    client = FakeOllamaClient({"message": {"content": "done"}})
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: client,
    )
    request = AssistantRequest(
        messages=_make_request().messages,
        tools=[
            ToolSpec(
                name="filesystem.read_file",
                description="Read",
                parameters_schema={"type": "object"},
            )
        ],
    )

    assistant.infer(request)

    assert client.calls[0]["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "filesystem__read_file",
                "description": "Read",
                "parameters": {"type": "object"},
            },
        }
    ]


def test_ollama_assistant_returns_tool_call_response():
    client = FakeOllamaClient(
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "id": "read-1",
                        "function": {
                            "name": "filesystem__read_file",
                            "arguments": {"path": "README.md"},
                        }
                    }
                ],
            }
        }
    )
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: client,
    )
    request = AssistantRequest(
        messages=_make_request().messages,
        tools=[ToolSpec(name="filesystem.read_file", description="Read", parameters_schema={})],
    )

    response = assistant.infer(request)

    assert response.kind == "tool_call"
    assert response.tool_name == "filesystem.read_file"
    assert response.tool_args == {"path": "README.md"}
    assert response.tool_call_id == "read-1"


def test_ollama_assistant_returns_message_response_without_tool_call():
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: FakeOllamaClient({"message": {"content": "hello"}}),
    )

    response = assistant.infer(_make_request())

    assert response.kind == "message"
    assert response.content == "hello"


def test_ollama_assistant_includes_tool_results_in_messages():
    client = FakeOllamaClient({"message": {"content": "done"}})
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: client,
    )
    tool_result_message = Message(
        type="message",
        role="assistant",
        created_at="2020-01-01T00:00:00Z",
        content=Content(
            items=[
                ToolResultMessage(
                    type="tool_result",
                    renderable=False,
                    data=ToolResult(
                        call_id="read-1",
                        status="ok",
                        result={"content": [{"type": "text", "text": "README content"}]},
                    ),
                )
            ]
        ),
        _meta=None,
    )

    assistant.infer(AssistantRequest(messages=[tool_result_message], tools=[]))

    assert client.calls[0]["messages"][0]["role"] == "tool"
    assert "README content" in client.calls[0]["messages"][0]["content"]


def test_ollama_assistant_serializes_tool_call_and_tool_result_messages():
    client = FakeOllamaClient({"message": {"content": "done"}})
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: client,
    )
    request = AssistantRequest(
        messages=[
            Message(
                type="message",
                role="user",
                created_at="2020-01-01T00:00:00Z",
                content=Content(
                    items=[
                        TextMessage(
                            type="text",
                            renderable=True,
                            data=TextContent(text="List files"),
                        )
                    ]
                ),
                _meta=None,
            ),
            Message(
                type="message",
                role="assistant",
                created_at="2020-01-01T00:00:01Z",
                content=Content(
                    items=[
                        ToolCallMessage(
                            type="tool_call",
                            renderable=False,
                            data=ToolCall(
                                call_id="call-1",
                                name="filesystem.read_file",
                                args={"path": "README.md"},
                            ),
                        )
                    ]
                ),
                _meta=None,
            ),
            Message(
                type="message",
                role="assistant",
                created_at="2020-01-01T00:00:02Z",
                content=Content(
                    items=[
                        ToolResultMessage(
                            type="tool_result",
                            renderable=False,
                            data=ToolResult(
                                call_id="call-1",
                                status="ok",
                                result={"content": [{"type": "text", "text": "README content"}]},
                            ),
                        )
                    ]
                ),
                _meta=None,
            ),
        ],
        tools=[
            ToolSpec(
                name="filesystem.read_file",
                description="Read",
                parameters_schema={"type": "object"},
            )
        ],
    )

    assistant.infer(request)

    assert client.calls[0]["messages"] == [
        {"role": "user", "content": "List files"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "filesystem__read_file",
                        "arguments": {"path": "README.md"},
                    }
                }
            ],
        },
        {
            "role": "tool",
            "content": '{"content": [{"type": "text", "text": "README content"}]}',
            "tool_name": "filesystem__read_file",
        },
    ]


def test_ollama_assistant_raises_clear_error_for_empty_message_after_tool_result():
    assistant = OllamaAssistant(
        model="test-model",
        client_factory=lambda host: FakeOllamaClient({"message": {"content": ""}}),
    )
    request = AssistantRequest(
        messages=[
            Message(
                type="message",
                role="assistant",
                created_at="2020-01-01T00:00:00Z",
                content=Content(
                    items=[
                        ToolResultMessage(
                            type="tool_result",
                            renderable=False,
                            data=ToolResult(
                                call_id="call-1",
                                status="ok",
                                result={"entries": []},
                            ),
                        )
                    ]
                ),
                _meta=None,
            )
        ],
        tools=[],
    )

    with pytest.raises(Exception, match="empty assistant response after tool execution"):
        assistant.infer(request)


def test_ollama_tool_support_error_is_mapped_to_clear_exception():
    assistant = OllamaAssistant(
        model="llama3:latest",
        client_factory=lambda host: RaisingOllamaClient(
            ollama.ResponseError(
                "registry.ollama.ai/library/llama3:latest does not support tools",
                400,
            )
        ),
    )

    with pytest.raises(ToolCallingNotSupportedError, match="does not support tool calling"):
        assistant.assert_tool_calling_supported()
