from dataclasses import dataclass

from ...domain.structured_data import StructuredMap

@dataclass(frozen=True)
class ChatResponse:
    chat_id: str
    content: str
    meta: StructuredMap
