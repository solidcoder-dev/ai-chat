from dataclasses import dataclass
from typing import Optional

from .token_counts import TokenCounts


@dataclass(frozen=True)
class Meta:
    client_msg_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[TokenCounts] = None
