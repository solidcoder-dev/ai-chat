from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..domain.workspace import Workspace
from ..infrastructure.mcp.mcp_server_config import McpServerConfig
from ..infrastructure.mcp.mcp_tool_adapter import McpToolAdapter
from ..infrastructure.mcp.mcp_tool_catalog import McpToolCatalog
from ..infrastructure.mcp.stdio_mcp_client import StdioMcpClient
from ..infrastructure.tool_registry import InMemoryToolRegistry


@dataclass(frozen=True)
class FilesystemMcpTooling:
    workspace: Workspace
    client: StdioMcpClient
    catalog: McpToolCatalog
    registry: InMemoryToolRegistry


def build_filesystem_mcp_tooling(
    workspace_path: str | Path,
    request_timeout_seconds: float = 30,
) -> FilesystemMcpTooling:
    workspace = Workspace(
        id="filesystem-workspace",
        name=Path(workspace_path).expanduser().resolve().name,
        root_path=workspace_path,
    )
    client = StdioMcpClient(
        McpServerConfig.filesystem("filesystem", workspace.root_path),
        request_timeout_seconds=request_timeout_seconds,
    )
    catalog = McpToolCatalog(namespace="filesystem", client=client)
    registry = InMemoryToolRegistry(
        {
            f"filesystem.{tool['name']}": McpToolAdapter(
                client=client,
                public_name=f"filesystem.{tool['name']}",
                mcp_tool_name=str(tool["name"]),
            )
            for tool in client.list_tools()
        }
    )
    return FilesystemMcpTooling(
        workspace=workspace,
        client=client,
        catalog=catalog,
        registry=registry,
    )
