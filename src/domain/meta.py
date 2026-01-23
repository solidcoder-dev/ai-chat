from dataclasses import dataclass
from typing import Optional

from .timing_ms import TimingMs
from .token_counts import TokenCounts


@dataclass(frozen=True)
class Meta:
    client_msg_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    model: Optional[str] = None
    agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    system_prompt_id: Optional[str] = None
    timing_ms: Optional[TimingMs] = None
    tokens: Optional[TokenCounts] = None
