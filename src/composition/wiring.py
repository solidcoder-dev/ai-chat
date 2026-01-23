from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine

from ..application.ports.tool_access_policy import ToolAccessPolicy
from ..application.ports.tool_catalog import ToolCatalog
from ..application.ports.tool_registry import ToolRegistry
from ..application.services.logging_assistant import LoggingAssistant
from ..application.services.metrics_assistant import MetricsAssistant
from ..application.services.orchestrated_chat_engine import OrchestratedChatEngine
from ..domain.repositories.chat_repo import ChatRepo
from ..domain.system_prompt import SystemPrompt
from ..infrastructure.data_catalog import PostgresDataCatalog
from ..infrastructure.inspect_schema_tool import InspectSchemaTool
from ..infrastructure.ollama_assistant import OllamaAssistant
from ..infrastructure.json_file_metrics import JsonFileMetrics
from ..infrastructure.postgres_chat_repo import PostgresChatRepo
from ..infrastructure.postgres_system_prompt_repo import PostgresSystemPromptRepo
from ..infrastructure.query_executor import SqlAlchemyQueryExecutor
from ..infrastructure.sql_execution_tool import SqlExecutionTool
from ..infrastructure.std_logger import StdLogger
from ..infrastructure.tool_access_policy import AllowAllToolAccessPolicy
from ..infrastructure.tool_catalog import create_default_tool_catalog
from ..infrastructure.tool_registry import InMemoryToolRegistry


def build_chat_engine(
    *,
    database_url: Optional[str] = None,
    ollama_model: str = "qwen2.5:0.5b",
) -> OrchestratedChatEngine:
    engine = create_engine(
        database_url
        or os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/ai_chat"),
        future=True,
    )

    chat_repo: ChatRepo = PostgresChatRepo(engine)
    system_prompt_repo = PostgresSystemPromptRepo(engine)
    data_catalog = PostgresDataCatalog(engine)
    query_executor = SqlAlchemyQueryExecutor(engine)

    tool_registry: ToolRegistry = InMemoryToolRegistry(
        {
            "inspect_schema": InspectSchemaTool(data_catalog),
            "sql_execute": SqlExecutionTool(query_executor),
        }
    )
    tool_catalog: ToolCatalog = create_default_tool_catalog()
    tool_access_policy: ToolAccessPolicy = AllowAllToolAccessPolicy()

    assistant = MetricsAssistant(
        LoggingAssistant(OllamaAssistant(model=ollama_model), StdLogger()),
        JsonFileMetrics(),
    )

    agent_id = os.environ.get("AGENT_ID", "assistant")
    agent_version = os.environ.get("AGENT_VERSION", "1.0.0")
    system_prompt_id = os.environ.get("SYSTEM_PROMPT_ID", "prompt-default")
    system_prompt_text = os.environ.get("SYSTEM_PROMPT_TEXT", "")

    system_prompt_repo.save_prompt(
        SystemPrompt(
            prompt_id=system_prompt_id,
            agent_id=agent_id,
            agent_version=agent_version,
            prompt_text=system_prompt_text,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    return OrchestratedChatEngine(
        chat_repo=chat_repo,
        assistant=assistant,
        tool_registry=tool_registry,
        tool_catalog=tool_catalog,
        tool_access_policy=tool_access_policy,
        agent_id=agent_id,
        agent_version=agent_version,
        system_prompt_id=system_prompt_id,
    )
