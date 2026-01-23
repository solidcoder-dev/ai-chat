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


@dataclass(frozen=True)


@dataclass(frozen=True)
class ImageContent(FileContent):
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass(frozen=True)
class ImageMessage:
    type: Literal["image"]
    renderable: Literal[True]
    data: ImageContent


@dataclass(frozen=True)
class AudioContent(FileContent):
    duration_ms: Optional[int] = None


@dataclass(frozen=True)
class AudioMessage:
    type: Literal["audio"]
    renderable: Literal[True]
    data: AudioContent


@dataclass(frozen=True)
class VideoContent(FileContent):
    duration_ms: Optional[int] = None


@dataclass(frozen=True)
class VideoMessage:
    type: Literal["video"]
    renderable: Literal[True]
    data: VideoContent
