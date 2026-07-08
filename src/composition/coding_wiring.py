from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..application.dtos.mcp_tool_descriptor import McpToolDescriptor
from ..application.ports.assistant import Assistant
from ..application.ports.mcp_client import McpClient
from ..application.ports.tool_access_policy import ToolAccessPolicy
from ..application.ports.tool_catalog import ToolCatalog
from ..application.ports.tool_registry import ToolRegistry
from ..application.services.orchestrated_chat_engine import OrchestratedChatEngine
from ..domain.repositories.chat_repo import ChatRepo
from ..domain.workspace import Workspace
from ..infrastructure.in_memory_chat_repo import InMemoryChatRepo
from ..infrastructure.mcp.mcp_server_config import McpServerConfig
from ..infrastructure.mcp.mcp_tool_catalog import McpToolCatalog
from ..infrastructure.mcp.mcp_tool_registry import McpToolRegistry
from ..infrastructure.mcp.stdio_mcp_client import StdioMcpClient
from ..infrastructure.ollama_assistant import OllamaAssistant
from ..infrastructure.tool_access_policy import AllowNamedToolsPolicy


READ_ONLY_FILESYSTEM_TOOL_NAMES = {
    "filesystem.read_file",
    "filesystem.read_multiple_files",
    "filesystem.list_directory",
    "filesystem.search_files",
    "filesystem.get_file_info",
    "filesystem.directory_tree",
}


@dataclass(frozen=True)
class FilesystemMcpTooling:
    workspace: Workspace
    client: McpClient
    catalog: ToolCatalog
    registry: ToolRegistry
    tool_access_policy: ToolAccessPolicy


def build_filesystem_mcp_tooling(
    workspace_path: str | Path,
    request_timeout_seconds: float = 30,
    client: McpClient | None = None,
    discovered_tools: Sequence[McpToolDescriptor] | None = None,
) -> FilesystemMcpTooling:
    workspace = Workspace(
        id="filesystem-workspace",
        name=Path(workspace_path).expanduser().resolve().name,
        root_path=workspace_path,
    )
    mcp_client = client or StdioMcpClient(
        McpServerConfig.filesystem("filesystem", workspace.root_path),
        request_timeout_seconds=request_timeout_seconds,
    )
    tools = list(
        mcp_client.list_tools() if discovered_tools is None else discovered_tools
    )
    catalog = McpToolCatalog(namespace="filesystem", tools=tools)
    registry = McpToolRegistry(namespace="filesystem", client=mcp_client, tools=tools)
    return FilesystemMcpTooling(
        workspace=workspace,
        client=mcp_client,
        catalog=catalog,
        registry=registry,
        tool_access_policy=AllowNamedToolsPolicy(READ_ONLY_FILESYSTEM_TOOL_NAMES),
    )


def build_coding_chat_engine(
    workspace_path: str | Path,
    assistant: Assistant | None = None,
    chat_repo: ChatRepo | None = None,
    mcp_client: McpClient | None = None,
    request_timeout_seconds: float = 30,
) -> OrchestratedChatEngine:
    tooling = build_filesystem_mcp_tooling(
        workspace_path=workspace_path,
        request_timeout_seconds=request_timeout_seconds,
        client=mcp_client,
    )
    return OrchestratedChatEngine(
        chat_repo=chat_repo or InMemoryChatRepo(),
        assistant=assistant or OllamaAssistant(),
        tool_registry=tooling.registry,
        tool_catalog=tooling.catalog,
        tool_access_policy=tooling.tool_access_policy,
    )
