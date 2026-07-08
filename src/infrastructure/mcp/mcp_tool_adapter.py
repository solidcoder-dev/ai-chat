from ...application.ports.mcp_client import McpClient
from ...application.ports.tool import Tool
from ...domain.structured_data import StructuredMap, StructuredValue


class McpToolAdapter(Tool):
    def __init__(
        self,
        client: McpClient,
        public_name: str,
        mcp_tool_name: str,
    ) -> None:
        self.public_name = public_name
        self._client = client
        self._mcp_tool_name = mcp_tool_name

    def run(self, args: StructuredMap) -> StructuredValue:
        return self._client.call_tool(self._mcp_tool_name, args)
