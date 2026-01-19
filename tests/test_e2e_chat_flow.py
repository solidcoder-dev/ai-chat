from typing import List

from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from src.application.dtos.assistant_request import AssistantRequest
from src.application.dtos.assistant_response import AssistantResponse
from src.application.dtos.tool_spec import ToolSpec
from src.application.ports.assistant import Assistant
from src.application.services.orchestrated_chat_engine import OrchestratedChatEngine
from src.infrastructure.data_catalog import PostgresDataCatalog
from src.infrastructure.inspect_schema_tool import InspectSchemaTool
from src.infrastructure.postgres_chat_repo import PostgresChatRepo
from src.infrastructure.query_executor import SqlAlchemyQueryExecutor
from src.infrastructure.sql_execution_tool import SqlExecutionTool
from src.infrastructure.tool_access_policy import AllowAllToolAccessPolicy
from src.infrastructure.tool_catalog import InMemoryToolCatalog
from src.infrastructure.tool_registry import InMemoryToolRegistry


class ScriptedAssistant(Assistant):
    def __init__(self, responses: List[AssistantResponse]) -> None:
        self._responses = responses
        self.requests: List[AssistantRequest] = []

    def infer(self, request: AssistantRequest) -> AssistantResponse:
        self.requests.append(request)
        return self._responses.pop(0)


def _seed(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)"))
        connection.execute(
            text("INSERT INTO items (id, name) VALUES (1, 'Alice'), (2, 'Bob')")
        )


def test_e2e_chat_flow_with_tools_and_postgres_repo():
    with PostgresContainer("postgres:16-alpine") as postgres:
        engine = create_engine(postgres.get_connection_url(), future=True)
        _seed(engine)

        data_catalog = PostgresDataCatalog(engine)
        query_executor = SqlAlchemyQueryExecutor(engine)
        tool_registry = InMemoryToolRegistry(
            {
                "inspect_schema": InspectSchemaTool(data_catalog),
                "sql_execute": SqlExecutionTool(query_executor),
            }
        )
        tool_catalog = InMemoryToolCatalog(
            [
                ToolSpec(name="inspect_schema", description="Schema", parameters_schema={}),
                ToolSpec(name="sql_execute", description="SQL", parameters_schema={}),
            ]
        )

        assistant = ScriptedAssistant(
            [
                AssistantResponse(
                    kind="tool_call",
                    content="",
                    tool_name="inspect_schema",
                    tool_args={"table_name": "items", "call_id": "call-1"},
                ),
                AssistantResponse(
                    kind="tool_call",
                    content="",
                    tool_name="sql_execute",
                    tool_args={"sql": "SELECT id, name FROM items ORDER BY id", "call_id": "call-2"},
                ),
                AssistantResponse(
                    kind="message",
                    content="done",
                    tool_name="",
                    tool_args={},
                ),
            ]
        )

        repo = PostgresChatRepo(engine)
        engine_service = OrchestratedChatEngine(
            chat_repo=repo,
            assistant=assistant,
            tool_registry=tool_registry,
            tool_catalog=tool_catalog,
            tool_access_policy=AllowAllToolAccessPolicy(),
        )

        response = engine_service.handle_user_message("chat-e2e", "run")
        assert response.content == "done"

        loaded = repo.load_chat("chat-e2e")
        messages = list(loaded.get_messages())
        assert len(messages) == 6
        assert messages[1].content.items[0].data.name == "inspect_schema"
        assert messages[2].content.items[0].data.call_id == "call-1"
        assert messages[3].content.items[0].data.name == "sql_execute"
        assert messages[4].content.items[0].data.call_id == "call-2"
        assert messages[5].content.items[0].data.text == "done"
