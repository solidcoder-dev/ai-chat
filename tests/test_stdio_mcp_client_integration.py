import shutil
import sys
from pathlib import Path

import pytest

from src.infrastructure.mcp.mcp_server_config import McpServerConfig
from src.infrastructure.mcp.stdio_mcp_client import McpConnectionError, StdioMcpClient


pytestmark = pytest.mark.integration
_filesystem_unavailable_reason = None


def require_npx():
    if shutil.which("npx") is None:
        pytest.skip("npx is not installed")


def filesystem_client(tmp_path):
    global _filesystem_unavailable_reason
    if _filesystem_unavailable_reason is not None:
        pytest.skip(_filesystem_unavailable_reason)
    require_npx()
    config = McpServerConfig.filesystem("filesystem", tmp_path)
    try:
        return StdioMcpClient(config, request_timeout_seconds=20)
    except McpConnectionError as exc:
        _filesystem_unavailable_reason = f"MCP filesystem server is unavailable: {exc}"
        pytest.skip(_filesystem_unavailable_reason)


def fake_client():
    fake_server = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"
    config = McpServerConfig(
        name="fake",
        command=sys.executable,
        args=["-u", str(fake_server)],
    )
    return StdioMcpClient(config, request_timeout_seconds=5)


def test_stdio_mcp_client_speaks_mcp_stdio_protocol(tmp_path):
    workspace_file = tmp_path / "notes.txt"
    workspace_file.write_text("hello from fake mcp", encoding="utf-8")
    client = fake_client()
    try:
        tool_names = {tool["name"] for tool in client.list_tools()}
        listing = client.call_tool("list_directory", {"path": str(tmp_path)})
        content = client.call_tool("read_file", {"path": str(workspace_file)})
    finally:
        client.close()

    assert {"read_file", "list_directory"} <= tool_names
    assert "notes.txt" in str(listing)
    assert "hello from fake mcp" in str(content)


def test_stdio_mcp_client_lists_filesystem_tools(tmp_path):
    client = filesystem_client(tmp_path)
    try:
        tool_names = {tool["name"] for tool in client.list_tools()}
    finally:
        client.close()

    assert {"read_file", "list_directory"} & tool_names


def test_stdio_mcp_client_can_list_workspace_directory(tmp_path):
    workspace_file = tmp_path / "notes.txt"
    workspace_file.write_text("hello", encoding="utf-8")
    client = filesystem_client(tmp_path)
    try:
        result = client.call_tool("list_directory", {"path": str(tmp_path)})
    finally:
        client.close()

    assert "notes.txt" in str(result)


def test_stdio_mcp_client_can_read_file_inside_workspace(tmp_path):
    workspace_file = tmp_path / "notes.txt"
    workspace_file.write_text("hello from mcp", encoding="utf-8")
    client = filesystem_client(tmp_path)
    try:
        result = client.call_tool("read_file", {"path": str(workspace_file)})
    finally:
        client.close()

    assert "hello from mcp" in str(result)


def test_stdio_mcp_client_reports_start_failure_cleanly():
    config = McpServerConfig(
        name="missing",
        command="definitely-not-an-mcp-command",
        args=[],
    )

    with pytest.raises(McpConnectionError, match="Failed to start MCP server"):
        StdioMcpClient(config)
