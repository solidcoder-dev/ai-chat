from typing import Dict, Sequence

from ..application.ports.tool import Tool
from ..application.ports.tool_registry import ToolRegistry


class InMemoryToolRegistry(ToolRegistry):
    def __init__(self, tools: Dict[str, Tool]) -> None:
        self._tools = tools

    def get_tool(self, name: str) -> Tool:
        return self._tools[name]


class CompositeToolRegistry(ToolRegistry):
    def __init__(self, registries: Sequence[ToolRegistry]) -> None:
        self._registries = list(registries)

    def get_tool(self, name: str) -> Tool:
        for registry in self._registries:
            try:
                return registry.get_tool(name)
            except KeyError:
                continue
        raise KeyError(name)
