from abc import ABC, abstractmethod
from typing import Sequence

from ..dtos.tool_spec import ToolSpec


class ToolCatalog(ABC):
    @abstractmethod
    def list_all_tool_specs(self) -> Sequence[ToolSpec]:
        raise NotImplementedError
