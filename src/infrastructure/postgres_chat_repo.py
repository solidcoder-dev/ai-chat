from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy import Column, MetaData, String, Table, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from ..domain.chat import Chat
from ..domain.file import (
    AudioContent,
    AudioMessage,
    FileContent,
    FileMessage,
    FileRef,
    ImageContent,
    ImageMessage,
    VideoContent,
    VideoMessage,
)
from ..domain.message import Content, Message, TextContent, TextMessage, ToolCallMessage, ToolResultMessage
from ..domain.meta import Meta
from ..domain.timing_ms import TimingMs
from ..domain.token_counts import TokenCounts
from ..domain.repositories.chat_repo import ChatRepo
from ..domain.tool import ToolCall, ToolResult


class PostgresChatRepo(ChatRepo):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = MetaData()
        self._chats = Table(
            "chats",
            self._metadata,
            Column("id", String, primary_key=True),
            Column("messages", JSONB, nullable=False),
        )
        self._metadata.create_all(self._engine)

    def load_chat(self, chat_id: str) -> Chat:
        with self._engine.begin() as connection:
            result = connection.execute(
                select(self._chats.c.messages).where(self._chats.c.id == chat_id)
            ).one_or_none()
        if result is None:
            return Chat(chat_id)
        messages = [self._deserialize_message(item) for item in result[0]]
        chat = Chat(chat_id)
        for message in messages:
            chat.add_message(message)
        return chat

    def save_chat(self, chat: Chat) -> None:
        messages_payload = [asdict(message) for message in chat.get_messages()]
        stmt = (
            insert(self._chats)
            .values(id=chat.id, messages=messages_payload)
            .on_conflict_do_update(
                index_elements=[self._chats.c.id],
                set_={"messages": messages_payload},
            )
        )
        with self._engine.begin() as connection:
            connection.execute(stmt)

    def _deserialize_message(self, payload: dict[str, Any]) -> Message:
        content = Content(items=[self._deserialize_part(part) for part in payload["content"]["items"]])
        meta = payload.get("_meta")
        return Message(
            type=payload["type"],
            role=payload["role"],
            created_at=payload["created_at"],
            content=content,
            _meta=self._deserialize_meta(meta) if meta is not None else None,
        )

    def _deserialize_part(self, payload: dict[str, Any]) -> object:
        part_type = payload["type"]
        data = payload["data"]
        if part_type == "text":
            return TextMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=TextContent(text=data["text"]),
            )
        if part_type == "file":
            return FileMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=self._deserialize_file_content(data),
            )
        if part_type == "image":
            return ImageMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=self._deserialize_image_content(data),
            )
        if part_type == "audio":
            return AudioMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=self._deserialize_audio_content(data),
            )
        if part_type == "video":
            return VideoMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=self._deserialize_video_content(data),
            )
        if part_type == "tool_call":
            return ToolCallMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=ToolCall(
                    call_id=data["call_id"],
                    name=data["name"],
                    args=data["args"],
                ),
            )
        if part_type == "tool_result":
            return ToolResultMessage(
                type=part_type,
                renderable=payload["renderable"],
                data=ToolResult(
                    call_id=data["call_id"],
                    status=data["status"],
                    result=data.get("result"),
                    error=data.get("error"),
                ),
            )
        raise ValueError(f"Unknown message part type: {part_type}")

    def _deserialize_file_ref(self, payload: dict[str, Any]) -> FileRef:
        return FileRef(
            source=payload["source"],
            media_type=payload["media_type"],
            uri=payload["uri"],
        )

    def _deserialize_file_content(self, payload: dict[str, Any]) -> FileContent:
        return FileContent(
            ref=self._deserialize_file_ref(payload["ref"]),
            filename=payload["filename"],
            bytes=payload.get("bytes"),
        )

    def _deserialize_image_content(self, payload: dict[str, Any]) -> ImageContent:
        return ImageContent(
            ref=self._deserialize_file_ref(payload["ref"]),
            filename=payload["filename"],
            bytes=payload.get("bytes"),
            width=payload.get("width"),
            height=payload.get("height"),
        )

    def _deserialize_audio_content(self, payload: dict[str, Any]) -> AudioContent:
        return AudioContent(
            ref=self._deserialize_file_ref(payload["ref"]),
            filename=payload["filename"],
            bytes=payload.get("bytes"),
            duration_ms=payload.get("duration_ms"),
        )

    def _deserialize_video_content(self, payload: dict[str, Any]) -> VideoContent:
        return VideoContent(
            ref=self._deserialize_file_ref(payload["ref"]),
            filename=payload["filename"],
            bytes=payload.get("bytes"),
            duration_ms=payload.get("duration_ms"),
        )

    def _deserialize_meta(self, payload: dict[str, Any]) -> Meta:
        timing = payload.get("timing_ms")
        tokens = payload.get("tokens")
        return Meta(
            client_msg_id=payload.get("client_msg_id"),
            request_id=payload.get("request_id"),
            trace_id=payload.get("trace_id"),
            model=payload.get("model"),
            timing_ms=self._deserialize_timing(timing) if timing else None,
            tokens=self._deserialize_tokens(tokens) if tokens else None,
        )

    def _deserialize_timing(self, payload: dict[str, Any]) -> TimingMs:
        return TimingMs(
            total=payload.get("total"),
            llm=payload.get("llm"),
            db=payload.get("db"),
            cache=payload.get("cache"),
            upload=payload.get("upload"),
        )

    def _deserialize_tokens(self, payload: dict[str, Any]) -> TokenCounts:
        return TokenCounts(
            input=payload.get("input"),
            output=payload.get("output"),
        )
