from __future__ import annotations

from typing import Mapping, Sequence, Union

Scalar = Union[str, int, float, bool, None]
StructuredValue = Union[Scalar, "StructuredMap", "StructuredList"]
StructuredMap = Mapping[str, StructuredValue]
StructuredList = Sequence[StructuredValue]
