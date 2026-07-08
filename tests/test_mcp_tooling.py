from pathlib import Path, PureWindowsPath

from src.application.dtos.mcp_tool_descriptor import McpToolDescriptor
from src.application.dtos.tool_spec import ToolSpec
from src.domain.workspace import Workspace
from src.infrastructure.mcp.mcp_server_config import McpServerConfig
from src.infrastructure.mcp.mcp_tool_adapter import McpToolAdapter
from src.infrastructure.mcp.mcp_tool_catalog import McpToolCatalog
from src.infrastructure.mcp.mcp_tool_registry import McpToolRegistry


class FakeMcpClient:
    def __init__(self) -> None:
        self.calls = []

    def list_tools(self):
        return [
            McpToolDescriptor(
                name="read_file",
                description="Read a file",
                parameters_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            ),
            McpToolDescriptor(
                name="list_directory",
                description="List a directory",
                parameters_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            ),
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"content": [{"type": "text", "text": "hello"}]}

    def close(self):
        pass


def test_workspace_normalizes_root_path(tmp_path):
    root = tmp_path / "project with spaces"
    root.mkdir()
    workspace = Workspace(id="workspace-1", name="Project", root_path=root / ".")

    assert isinstance(workspace.root_path, Path)
    assert workspace.root_path == root.resolve()
    assert str(PureWindowsPath("C:/Users/Ada/project with spaces")).endswith(
        "project with spaces"
    )


def test_mcp_tool_adapter_calls_underlying_mcp_tool_name():
    client = FakeMcpClient()
    adapter = McpToolAdapter(
        client=client,
        public_name="filesystem.read_file",
        mcp_tool_name="read_file",
    )

    adapter.run({"path": "README.md"})

    assert client.calls == [("read_file", {"path": "README.md"})]


def test_mcp_tool_adapter_returns_tool_result():
    adapter = McpToolAdapter(
        client=FakeMcpClient(),
        public_name="filesystem.read_file",
        mcp_tool_name="read_file",
    )

    result = adapter.run({"path": "README.md"})

    assert result == {"content": [{"type": "text", "text": "hello"}]}


def test_mcp_tool_catalog_prefixes_tool_names():
    catalog = McpToolCatalog(namespace="filesystem", tools=FakeMcpClient().list_tools())

    names = [spec.name for spec in catalog.list_all_tool_specs()]

    assert names == ["filesystem.read_file", "filesystem.list_directory"]


def test_mcp_tool_catalog_preserves_description_and_schema():
    catalog = McpToolCatalog(namespace="filesystem", tools=FakeMcpClient().list_tools())

    specs = catalog.list_all_tool_specs()

    assert specs[0] == ToolSpec(
        name="filesystem.read_file",
        description="Read a file",
        parameters_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )


def test_mcp_client_lists_typed_tool_descriptors():
    tools = FakeMcpClient().list_tools()

    assert all(isinstance(tool, McpToolDescriptor) for tool in tools)


def test_mcp_tool_catalog_uses_tool_descriptors():
    descriptor = McpToolDescriptor(
        name="read_file",
        description="Read a file",
        parameters_schema={"type": "object"},
    )
    catalog = McpToolCatalog(namespace="filesystem", tools=[descriptor])

    assert catalog.list_all_tool_specs() == [
        ToolSpec(
            name="filesystem.read_file",
            description="Read a file",
            parameters_schema={"type": "object"},
        )
    ]


def test_mcp_tool_registry_uses_same_tool_snapshot_as_catalog():
    client = FakeMcpClient()
    tools = client.list_tools()
    catalog = McpToolCatalog(namespace="filesystem", tools=tools)
    registry = McpToolRegistry(namespace="filesystem", client=client, tools=tools)

    names = [spec.name for spec in catalog.list_all_tool_specs()]
    registry.get_tool("filesystem.read_file").run({"path": "README.md"})

    assert names == ["filesystem.read_file", "filesystem.list_directory"]
    assert client.calls == [("read_file", {"path": "README.md"})]


def test_mcp_server_config_builds_stdio_command_without_shell(tmp_path):
    config = McpServerConfig.filesystem("filesystem", tmp_path)

    assert config.command == "npx"
    assert config.args == [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        str(tmp_path.resolve()),
    ]
    assert " " not in config.command
