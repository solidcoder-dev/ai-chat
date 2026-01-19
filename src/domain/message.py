from dataclasses import dataclass
from typing import Literal, Optional, Sequence, Union

from .file import AudioMessage, FileMessage, ImageMessage, VideoMessage
from .meta import Meta
from .tool import ToolCall, ToolResult


@dataclass(frozen=True)
class Content:
    items: Sequence["MessagePart"]


@dataclass(frozen=True)
class TextContent:
    text: str


@dataclass(frozen=True)
class TextMessage:
    type: Literal["text"]
    renderable: Literal[True]
    data: TextContent


@dataclass(frozen=True)
class ToolCallMessage:
    type: Literal["tool_call"]
    renderable: Literal[False]
    data: ToolCall


@dataclass(frozen=True)
class ToolResultMessage:
    type: Literal["tool_result"]
    renderable: Literal[False]
    data: ToolResult


MessagePart = Union[
    TextMessage,
    ImageMessage,
    AudioMessage,
    VideoMessage,
    FileMessage,
    ToolCallMessage,
    ToolResultMessage,
]


@dataclass(frozen=True)
class Message:
    type: Literal["message"]
    role: Literal["user", "assistant", "system"]
    created_at: str
    content: Content
    _meta: Optional[Meta] = None
