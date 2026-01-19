from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TokenCounts:
    input: Optional[int] = None
    output: Optional[int] = None
