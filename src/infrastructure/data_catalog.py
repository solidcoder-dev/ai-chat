from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..application.dtos.schema import Schema
from ..application.dtos.table_info import TableInfo
from ..application.ports.data_catalog import DataCatalog


class PostgresDataCatalog(DataCatalog):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_table_for_dataset(self, name: str) -> TableInfo:
        with self._engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_name = :table_name
                    ORDER BY table_schema
                    LIMIT 1
                    """
                ),
                {"table_name": name},
            ).one_or_none()
        if result is None:
            return TableInfo(dataset_name="", table_name=name)
        return TableInfo(dataset_name=result[0], table_name=result[1])

    def get_schema(self, table_name: str) -> Schema:
        columns = self._get_columns(table_name, None)
        return Schema(columns=columns)

    def _get_columns(self, table_name: str, schema: Optional[str]) -> list[str]:
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
        """
        params = {"table_name": table_name}
        if schema:
            query += " AND table_schema = :table_schema"
            params["table_schema"] = schema
        query += " ORDER BY ordinal_position"
        with self._engine.begin() as connection:
            result = connection.execute(text(query), params).all()
        return [row[0] for row in result]
