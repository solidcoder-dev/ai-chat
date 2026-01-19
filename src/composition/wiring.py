from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine

from ..application.ports.tool_access_policy import ToolAccessPolicy
from ..application.ports.tool_catalog import ToolCatalog
from ..application.ports.tool_registry import ToolRegistry
from ..application.services.orchestrated_chat_engine import OrchestratedChatEngine
from ..domain.repositories.chat_repo import ChatRepo
from ..infrastructure.data_catalog import PostgresDataCatalog
from ..infrastructure.inspect_schema_tool import InspectSchemaTool
from ..infrastructure.ollama_assistant import OllamaAssistant
from ..infrastructure.postgres_chat_repo import PostgresChatRepo
from ..infrastructure.query_executor import SqlAlchemyQueryExecutor
from ..infrastructure.sql_execution_tool import SqlExecutionTool
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

    assistant = OllamaAssistant(model=ollama_model)

    return OrchestratedChatEngine(
        chat_repo=chat_repo,
        assistant=assistant,
        tool_registry=tool_registry,
        tool_catalog=tool_catalog,
        tool_access_policy=tool_access_policy,
    )
