from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class FileContent:
    source: Literal["uri", "base64"]
    media_type: str
    uri: str
    filename: str
    bytes: Optional[int] = None


@dataclass(frozen=True)
class FileMessage:
    type: Literal["file"]
    renderable: Literal[True]
    data: FileContent
