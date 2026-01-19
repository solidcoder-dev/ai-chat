import pytest

from src.application.dtos.assistant_request import AssistantRequest
from src.application.errors import ModelNotAvailableError
from src.domain.message import Content, Message, TextContent, TextMessage
from src.infrastructure.ollama_assistant import OllamaAssistant


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
