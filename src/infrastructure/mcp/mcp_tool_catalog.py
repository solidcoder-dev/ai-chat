from typing import Sequence

from ...application.dtos.tool_spec import ToolSpec
from ...application.ports.mcp_client import McpClient
from ...application.ports.tool_catalog import ToolCatalog


class McpToolCatalog(ToolCatalog):
    def __init__(self, namespace: str, client: McpClient) -> None:
        self._namespace = namespace
        self._client = client

    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        return [self._to_tool_spec(tool) for tool in self._client.list_tools()]

    def _to_tool_spec(self, tool) -> ToolSpec:
        name = str(tool["name"])
        return ToolSpec(
            name=f"{self._namespace}.{name}",
            description=str(tool.get("description", "")),
            parameters_schema=tool.get("inputSchema", {}),
        )
