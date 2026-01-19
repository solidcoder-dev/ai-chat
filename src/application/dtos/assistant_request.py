from dataclasses import dataclass
from typing import Sequence

from ...domain.message import Message
from .tool_spec import ToolSpec


@dataclass(frozen=True)
class AssistantRequest:
    messages: Sequence[Message]
    tools: Sequence[ToolSpec]
