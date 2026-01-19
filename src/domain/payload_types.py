from __future__ import annotations

from typing import Mapping, Sequence, Union

Primitive = Union[str, int, float, bool, None]
PayloadValue = Union[Primitive, "PayloadObject", "PayloadArray"]
PayloadObject = Mapping[str, PayloadValue]
PayloadArray = Sequence[PayloadValue]
