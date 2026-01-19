from dataclasses import dataclass

from ...domain.structured_data import StructuredMap

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters_schema: StructuredMap
