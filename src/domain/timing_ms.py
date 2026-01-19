from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TimingMs:
    total: Optional[float] = None
    llm: Optional[float] = None
    db: Optional[float] = None
    cache: Optional[float] = None
    upload: Optional[float] = None
