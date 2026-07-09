from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Sequence

from ..application.dtos.mcp_tool_descriptor import McpToolDescriptor
from ..application.dtos.tool_spec import ToolSpec
from ..application.ports.assistant import Assistant
from ..application.ports.mcp_client import McpClient
from ..application.ports.tool_access_policy import ToolAccessPolicy
from ..application.ports.tool_catalog import ToolCatalog
from ..application.ports.tool_registry import ToolRegistry
from ..application.services.patch_proposal_service import PatchProposalService
from ..application.services.orchestrated_chat_engine import OrchestratedChatEngine
from ..domain.repositories.chat_repo import ChatRepo
from ..domain.workspace import Workspace
from ..infrastructure.in_memory_chat_repo import InMemoryChatRepo
from ..infrastructure.mcp.mcp_server_config import McpServerConfig
from ..infrastructure.mcp.mcp_tool_catalog import McpToolCatalog
from ..infrastructure.mcp.mcp_tool_registry import McpToolRegistry
from ..infrastructure.mcp.stdio_mcp_client import StdioMcpClient
from ..infrastructure.ollama_assistant import OllamaAssistant
from ..infrastructure.patch_proposal_repository import InMemoryPatchProposalRepository
from ..infrastructure.propose_edit_tool import ProposeEditTool
from ..infrastructure.tool_access_policy import AllowNamedToolsPolicy
from ..infrastructure.tool_catalog import CompositeToolCatalog, InMemoryToolCatalog
from ..infrastructure.tool_registry import CompositeToolRegistry, InMemoryToolRegistry


DEFAULT_CODING_MODEL = "llama3.1:8b"


SAFE_CODING_TOOL_NAMES = {
    "filesystem.read_file",
    "filesystem.read_multiple_files",
    "filesystem.list_directory",
    "filesystem.search_files",
    "filesystem.get_file_info",
    "filesystem.directory_tree",
    "filesystem.propose_edit",
}


@dataclass(frozen=True)
class FilesystemMcpTooling:
    workspace: Workspace
    client: McpClient
    catalog: ToolCatalog
    registry: ToolRegistry
    tool_access_policy: ToolAccessPolicy


@dataclass(frozen=True)
class CodingChatSession:
    workspace: Workspace
    engine: OrchestratedChatEngine
    mcp_client: McpClient

    def close(self) -> None:
        self.mcp_client.close()


def resolve_coding_model(model: str | None = None) -> str:
    if model:
        return model
    return os.environ.get("OLLAMA_MODEL", DEFAULT_CODING_MODEL)


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
    mcp_catalog = McpToolCatalog(namespace="filesystem", tools=tools)
    mcp_registry = McpToolRegistry(namespace="filesystem", client=mcp_client, tools=tools)
    propose_edit_catalog = InMemoryToolCatalog([_propose_edit_tool_spec()])
    propose_edit_registry = InMemoryToolRegistry(
        {
            "filesystem.propose_edit": ProposeEditTool(
                PatchProposalService(
                    workspace=workspace,
                    proposals=InMemoryPatchProposalRepository(),
                )
            )
        }
    )
    return FilesystemMcpTooling(
        workspace=workspace,
        client=mcp_client,
        catalog=CompositeToolCatalog([mcp_catalog, propose_edit_catalog]),
        registry=CompositeToolRegistry([mcp_registry, propose_edit_registry]),
        tool_access_policy=AllowNamedToolsPolicy(SAFE_CODING_TOOL_NAMES),
    )


def build_coding_chat_engine(
    workspace_path: str | Path,
    model: str | None = None,
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
        assistant=assistant or OllamaAssistant(model=resolve_coding_model(model)),
        tool_registry=tooling.registry,
        tool_catalog=tooling.catalog,
        tool_access_policy=tooling.tool_access_policy,
    )


def build_coding_chat_session(
    workspace_path: str | Path,
    model: str | None = None,
    assistant: Assistant | None = None,
    chat_repo: ChatRepo | None = None,
    mcp_client: McpClient | None = None,
    request_timeout_seconds: float = 30,
) -> CodingChatSession:
    tooling = build_filesystem_mcp_tooling(
        workspace_path=workspace_path,
        request_timeout_seconds=request_timeout_seconds,
        client=mcp_client,
    )
    selected_assistant = assistant or OllamaAssistant(model=resolve_coding_model(model))
    try:
        if isinstance(selected_assistant, OllamaAssistant):
            selected_assistant.assert_tool_calling_supported()
        engine = OrchestratedChatEngine(
            chat_repo=chat_repo or InMemoryChatRepo(),
            assistant=selected_assistant,
            tool_registry=tooling.registry,
            tool_catalog=tooling.catalog,
            tool_access_policy=tooling.tool_access_policy,
        )
        return CodingChatSession(
            workspace=tooling.workspace,
            engine=engine,
            mcp_client=tooling.client,
        )
    except Exception:
        tooling.client.close()
        raise


def _propose_edit_tool_spec() -> ToolSpec:
    return ToolSpec(
        name="filesystem.propose_edit",
        description="Propose a file replacement as a unified diff without modifying files.",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "new_content": {"type": "string"},
            },
            "required": ["path", "new_content"],
            "additionalProperties": False,
        },
    )
