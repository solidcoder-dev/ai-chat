from dataclasses import dataclass
from typing import Mapping, Sequence

from ...domain.structured_data import StructuredValue

@dataclass(frozen=True)
class QueryResult:
    rows: Sequence[Mapping[str, StructuredValue]]
