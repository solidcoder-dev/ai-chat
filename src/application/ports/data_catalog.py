from abc import ABC, abstractmethod

from ..dtos.schema import Schema
from ..dtos.table_info import TableInfo


class DataCatalog(ABC):
    @abstractmethod
    def get_table_for_dataset(self, name: str) -> TableInfo:
        raise NotImplementedError

    @abstractmethod
    def get_schema(self, table_name: str) -> Schema:
        raise NotImplementedError
