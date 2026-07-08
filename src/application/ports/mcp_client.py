from abc import ABC, abstractmethod
from typing import Sequence

from ...domain.structured_data import StructuredMap, StructuredValue


class McpClient(ABC):
    @abstractmethod
    def list_tools(self) -> Sequence[StructuredMap]:
        raise NotImplementedError

    @abstractmethod
    def call_tool(self, name: str, arguments: StructuredMap) -> StructuredValue:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
