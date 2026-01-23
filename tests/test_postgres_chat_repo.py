from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from src.domain.chat import Chat
from src.domain.message import Content, Message, TextContent, TextMessage
from src.infrastructure.postgres_chat_repo import PostgresChatRepo


def _seed_dependencies(engine, *, user_id: str, prompt_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO company (id, name, status, created_at)
                VALUES ('company-1', 'Demo', 'active', :created_at)
                """
            ),
            {"created_at": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO office (id, company_id, name, status, created_at)
                VALUES ('office-1', 'company-1', 'HQ', 'active', :created_at)
                """
            ),
            {"created_at": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO app_user (id, company_id, office_id, status, created_at)
                VALUES (:user_id, 'company-1', 'office-1', 'active', :created_at)
                """
            ),
            {"user_id": user_id, "created_at": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO system_prompt (id, agent_id, agent_version, prompt_text, created_at)
                VALUES (:prompt_id, 'agent-1', '1.0.0', 'system prompt', :created_at)
                """
            ),
            {"prompt_id": prompt_id, "created_at": now},
        )


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
        _seed_dependencies(engine, user_id="user-1", prompt_id="prompt-1")
        chat = Chat(
            "chat-1",
            user_id="user-1",
            agent_id="agent-1",
            agent_version="1.0.0",
            system_prompt_id="prompt-1",
        )
        chat.add_message(_make_message("hello"))
        repo.save_chat(chat)

        loaded = repo.load_chat("chat-1")
        messages = list(loaded.get_messages())
        assert loaded.id == "chat-1"
        assert len(messages) == 1
        assert messages[0].content.items[0].data.text == "hello"
