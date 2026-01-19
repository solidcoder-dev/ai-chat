from src.application.dtos.tool_spec import ToolSpec
from src.infrastructure.tool_access_policy import AllowAllToolAccessPolicy
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
