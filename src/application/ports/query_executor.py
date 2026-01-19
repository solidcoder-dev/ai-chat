from abc import ABC, abstractmethod

from ..dtos.query_result import QueryResult


class QueryExecutor(ABC):
    @abstractmethod
    def execute(self, sql: str) -> QueryResult:
        raise NotImplementedError
