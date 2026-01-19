from dataclasses import dataclass
from typing import Literal, Optional

from .structured_data import StructuredMap, StructuredValue


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    args: StructuredMap


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    status: Literal["ok", "error"]
    result: Optional[StructuredValue] = None
    error: Optional[StructuredMap] = None
