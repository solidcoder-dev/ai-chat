from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from src.infrastructure.data_catalog import PostgresDataCatalog
from src.infrastructure.inspect_schema_tool import InspectSchemaTool
from src.infrastructure.query_executor import SqlAlchemyQueryExecutor
from src.infrastructure.sql_execution_tool import SqlExecutionTool


def _seed(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)"))
        connection.execute(
            text("INSERT INTO items (id, name) VALUES (1, 'Alice'), (2, 'Bob')")
        )


def test_inspect_schema_tool():
    with PostgresContainer("postgres:16-alpine") as postgres:
        engine = create_engine(postgres.get_connection_url(), future=True)
        _seed(engine)

        catalog = PostgresDataCatalog(engine)
        tool = InspectSchemaTool(catalog)
        result = tool.run({"table_name": "items"})

        assert result["table_name"] == "items"
        assert "id" in result["columns"]
        assert "name" in result["columns"]


def test_sql_execution_tool():
    with PostgresContainer("postgres:16-alpine") as postgres:
        engine = create_engine(postgres.get_connection_url(), future=True)
        _seed(engine)

        executor = SqlAlchemyQueryExecutor(engine)
        tool = SqlExecutionTool(executor)
        result = tool.run({"sql": "SELECT id, name FROM items ORDER BY id"})

        assert result["rows"] == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
