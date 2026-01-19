from typing import Dict

from ..application.ports.tool import Tool
from ..application.ports.tool_registry import ToolRegistry


class InMemoryToolRegistry(ToolRegistry):
    def __init__(self, tools: Dict[str, Tool]) -> None:
        self._tools = tools

    def get_tool(self, name: str) -> Tool:
        return self._tools[name]
