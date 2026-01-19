from typing import Sequence

from ..application.dtos.tool_spec import ToolSpec
from ..application.ports.tool_access_policy import ToolAccessPolicy
from ..domain.structured_data import StructuredValue


class AllowAllToolAccessPolicy(ToolAccessPolicy):
    def get_allowed_tools(
        self,
        assistant_id: str,
        context: StructuredValue,
        all_specs: Sequence[ToolSpec],
    ) -> Sequence[ToolSpec]:
        return list(all_specs)
