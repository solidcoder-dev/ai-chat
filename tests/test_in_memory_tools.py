from src.application.dtos.tool_spec import ToolSpec
from src.infrastructure.tool_access_policy import AllowAllToolAccessPolicy, AllowNamedToolsPolicy
from src.infrastructure.tool_catalog import InMemoryToolCatalog, create_default_tool_catalog
from src.infrastructure.tool_registry import InMemoryToolRegistry


class DummyTool:
    def run(self, args):
        return {"ok": True}


def test_in_memory_tool_catalog():
    specs = [ToolSpec(name="t1", description="d1", parameters_schema={})]
    catalog = InMemoryToolCatalog(specs)
    assert catalog.list_all_tool_specs() == specs


def test_default_tool_catalog_contains_known_tools():
    catalog = create_default_tool_catalog()
    names = [spec.name for spec in catalog.list_all_tool_specs()]
    assert "inspect_schema" in names
    assert "sql_execute" in names


def test_in_memory_tool_registry():
    tool = DummyTool()
    registry = InMemoryToolRegistry({"t1": tool})
    assert registry.get_tool("t1") is tool


def test_allow_all_tool_access_policy():
    specs = [
        ToolSpec(name="t1", description="d1", parameters_schema={}),
        ToolSpec(name="t2", description="d2", parameters_schema={}),
    ]
    policy = AllowAllToolAccessPolicy()
    assert policy.get_allowed_tools("assistant-1", {}, specs) == specs


def test_allow_named_tools_policy_allows_only_explicit_names():
    specs = [
        ToolSpec(name="filesystem.read_file", description="Read", parameters_schema={}),
        ToolSpec(name="filesystem.write_file", description="Write", parameters_schema={}),
    ]
    policy = AllowNamedToolsPolicy({"filesystem.read_file"})

    allowed = policy.get_allowed_tools("assistant-1", {}, specs)

    assert [spec.name for spec in allowed] == ["filesystem.read_file"]


def test_allow_named_tools_policy_blocks_filesystem_write_tools():
    specs = [
        ToolSpec(name="filesystem.write_file", description="Write", parameters_schema={}),
        ToolSpec(name="filesystem.edit_file", description="Edit", parameters_schema={}),
        ToolSpec(name="filesystem.move_file", description="Move", parameters_schema={}),
        ToolSpec(name="filesystem.create_directory", description="Create", parameters_schema={}),
        ToolSpec(name="filesystem.read_file", description="Read", parameters_schema={}),
    ]
    policy = AllowNamedToolsPolicy({"filesystem.read_file"})

    allowed = policy.get_allowed_tools("assistant-1", {}, specs)

    assert [spec.name for spec in allowed] == ["filesystem.read_file"]


def test_allow_named_tools_policy_returns_empty_list_when_no_tools_are_allowed():
    specs = [ToolSpec(name="filesystem.write_file", description="Write", parameters_schema={})]
    policy = AllowNamedToolsPolicy({"filesystem.read_file"})

    assert policy.get_allowed_tools("assistant-1", {}, specs) == []
