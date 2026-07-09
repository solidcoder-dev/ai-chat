from dataclasses import dataclass

from ...domain.structured_data import StructuredMap

@dataclass(frozen=True)
class AssistantResponse:
    kind: str
    content: str
    tool_name: str
    tool_args: StructuredMap
    tool_call_id: str | None = None
