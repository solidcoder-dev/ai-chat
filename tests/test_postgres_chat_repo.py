from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

from src.domain.chat import Chat
from src.domain.message import Content, Message, TextContent, TextMessage
from src.infrastructure.postgres_chat_repo import PostgresChatRepo


def _make_message(text: str) -> Message:
    return Message(
        type="message",
        role="user",
        created_at="2024-01-01T00:00:00Z",
        content=Content(
            items=[
                TextMessage(
                    type="text",
                    renderable=True,
                    data=TextContent(text=text),
                )
            ]
        ),
        _meta=None,
    )


def test_postgres_chat_repo_round_trip():
    with PostgresContainer("postgres:16-alpine") as postgres:
        engine = create_engine(postgres.get_connection_url(), future=True)
        repo = PostgresChatRepo(engine)
        chat = Chat("chat-1")
        chat.add_message(_make_message("hello"))
        repo.save_chat(chat)

        loaded = repo.load_chat("chat-1")
        messages = list(loaded.get_messages())
        assert loaded.id == "chat-1"
        assert len(messages) == 1
        assert messages[0].content.items[0].data.text == "hello"
