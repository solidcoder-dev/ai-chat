from abc import ABC, abstractmethod

from .tool import Tool


class ToolRegistry(ABC):
    @abstractmethod
    def get_tool(self, name: str) -> Tool:
        raise NotImplementedError
