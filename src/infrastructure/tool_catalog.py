from typing import Sequence

from ..application.dtos.tool_spec import ToolSpec
from ..application.ports.tool_catalog import ToolCatalog
from .tool_specs import default_tool_specs


class InMemoryToolCatalog(ToolCatalog):
    def __init__(self, specs: Sequence[ToolSpec]) -> None:
        self._specs = list(specs)

    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        return list(self._specs)


class CompositeToolCatalog(ToolCatalog):
    def __init__(self, catalogs: Sequence[ToolCatalog]) -> None:
        self._catalogs = list(catalogs)

    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        specs: list[ToolSpec] = []
        for catalog in self._catalogs:
            specs.extend(catalog.list_all_tool_specs())
        return specs


def create_default_tool_catalog() -> InMemoryToolCatalog:
    return InMemoryToolCatalog(default_tool_specs())
