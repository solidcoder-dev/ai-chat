import pytest

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.tool_spec import ToolSpec
from src.application.errors import ModelNotAvailableError
from src.domain.message import Content, Message, TextContent, TextMessage
from src.domain.message import ToolResultMessage
from src.domain.tool import ToolResult
from src.infrastructure.ollama_assistant import OllamaAssistant


class FakeOllamaClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


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

    assert "README content" in client.calls[0]["messages"][0]["content"]
