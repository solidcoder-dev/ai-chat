from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table, Text, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from ..domain.repositories.system_prompt_repo import SystemPromptRepo
from ..domain.system_prompt import SystemPrompt


class PostgresSystemPromptRepo(SystemPromptRepo):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = MetaData()
        self._prompts = Table(
            "system_prompt",
            self._metadata,
            Column("id", String, primary_key=True),
            Column("agent_id", String, nullable=False),
            Column("agent_version", String, nullable=False),
            Column("prompt_text", Text, nullable=False),
            Column("prompt_hash", String, nullable=True),
            Column("created_at", String, nullable=True),
        )
        self._metadata.create_all(self._engine)

    def load_prompt(self, prompt_id: str) -> SystemPrompt:
        with self._engine.begin() as connection:
            result = connection.execute(
                select(
                    self._prompts.c.id,
                    self._prompts.c.agent_id,
                    self._prompts.c.agent_version,
                    self._prompts.c.prompt_text,
                    self._prompts.c.prompt_hash,
                    self._prompts.c.created_at,
                ).where(self._prompts.c.id == prompt_id)
            ).one_or_none()
        if result is None:
            raise ValueError(f"System prompt not found: {prompt_id}")
        return SystemPrompt(
            prompt_id=result[0],
            agent_id=result[1],
            agent_version=result[2],
            prompt_text=result[3],
            prompt_hash=result[4],
            created_at=result[5],
        )

    def save_prompt(self, prompt: SystemPrompt) -> None:
        stmt = (
            insert(self._prompts)
            .values(
                id=prompt.prompt_id,
                agent_id=prompt.agent_id,
                agent_version=prompt.agent_version,
                prompt_text=prompt.prompt_text,
                prompt_hash=prompt.prompt_hash,
                created_at=prompt.created_at,
            )
            .on_conflict_do_update(
                index_elements=[self._prompts.c.id],
                set_={
                    "agent_id": prompt.agent_id,
                    "agent_version": prompt.agent_version,
                    "prompt_text": prompt.prompt_text,
                    "prompt_hash": prompt.prompt_hash,
                    "created_at": prompt.created_at,
                },
            )
        )
        with self._engine.begin() as connection:
            connection.execute(stmt)
