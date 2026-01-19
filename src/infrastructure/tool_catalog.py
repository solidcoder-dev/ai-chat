from typing import Sequence

from ..application.dtos.tool_spec import ToolSpec
from ..application.ports.tool_catalog import ToolCatalog


class InMemoryToolCatalog(ToolCatalog):
    def __init__(self, specs: Sequence[ToolSpec]) -> None:
        self._specs = list(specs)

    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        return list(self._specs)
