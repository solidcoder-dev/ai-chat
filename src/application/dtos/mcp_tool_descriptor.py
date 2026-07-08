from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class McpToolDescriptor:
    name: str
    description: str
    parameters_schema: Mapping[str, Any]
