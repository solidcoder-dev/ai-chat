from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass(frozen=True)
class Workspace:
    id: str
    name: str
    root_path: Path

    def __init__(self, id: str, name: str, root_path: Union[str, Path]) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "root_path", Path(root_path).expanduser().resolve())
