from abc import ABC, abstractmethod
from typing import Sequence

from ..dtos.tool_spec import ToolSpec
from ...domain.structured_data import StructuredValue


class ToolAccessPolicy(ABC):
    @abstractmethod
    def get_allowed_tools(
        self,
        assistant_id: str,
        context: StructuredValue,
        all_specs: Sequence[ToolSpec],
    ) -> Sequence[ToolSpec]:
        raise NotImplementedError
