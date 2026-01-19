from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..application.dtos.query_result import QueryResult
from ..application.ports.query_executor import QueryExecutor


class SqlAlchemyQueryExecutor(QueryExecutor):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def execute(self, sql: str) -> QueryResult:
        with self._engine.begin() as connection:
            result = connection.execute(text(sql))
            rows = [dict(row) for row in result.mappings().all()]
        return QueryResult(rows=rows)
