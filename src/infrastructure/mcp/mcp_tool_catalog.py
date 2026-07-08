from typing import Sequence

from ...application.dtos.mcp_tool_descriptor import McpToolDescriptor
from ...application.dtos.tool_spec import ToolSpec
from ...application.ports.tool_catalog import ToolCatalog


class McpToolCatalog(ToolCatalog):
    def __init__(self, namespace: str, tools: Sequence[McpToolDescriptor]) -> None:
        self._namespace = namespace
        self._tools = list(tools)

    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        return [self._to_tool_spec(tool) for tool in self._tools]

    def _to_tool_spec(self, tool: McpToolDescriptor) -> ToolSpec:
        return ToolSpec(
            name=f"{self._namespace}.{tool.name}",
            description=tool.description,
            parameters_schema=tool.parameters_schema,
        )
