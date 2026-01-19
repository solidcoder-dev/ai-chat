import pytest

from src.application.dtos.assistant_request import AssistantRequest
from src.application.errors import ModelNotAvailableError
from src.application.services.multi_assistant import MultiAssistant
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


def test_multi_assistant_fallback_to_second(ollama_ready) -> None:
    bad = OllamaAssistant(model="missing-model-for-test")
    good = OllamaAssistant(model=ollama_ready["model"])
    multi = MultiAssistant(
        [bad, good],
        recoverable_exceptions=(ModelNotAvailableError,),
    )

    response = multi.infer(_make_request())
    assert response.kind == "message"
    assert response.content


def test_multi_assistant_without_children_raises() -> None:
    multi = MultiAssistant([])
    with pytest.raises(ValueError):
        multi.infer(_make_request())
