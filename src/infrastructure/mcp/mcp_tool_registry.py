from typing import Sequence

from ...application.dtos.mcp_tool_descriptor import McpToolDescriptor
from ...application.ports.mcp_client import McpClient
from ...application.ports.tool import Tool
from ...application.ports.tool_registry import ToolRegistry
from .mcp_tool_adapter import McpToolAdapter


class McpToolRegistry(ToolRegistry):
    def __init__(
        self,
        namespace: str,
        client: McpClient,
        tools: Sequence[McpToolDescriptor],
    ) -> None:
        self._tools = {
            f"{namespace}.{tool.name}": McpToolAdapter(
                client=client,
                public_name=f"{namespace}.{tool.name}",
                mcp_tool_name=tool.name,
            )
            for tool in tools
        }

    def get_tool(self, name: str) -> Tool:
        return self._tools[name]
