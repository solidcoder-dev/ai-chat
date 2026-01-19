from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Schema:
    columns: Sequence[str]
