from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4
import threading
import weakref

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy import event

from ..domain.chat import Chat
from ..domain.file import FileContent, FileMessage
from ..domain.message import (
    Content,
    Message,
    TextContent,
    TextMessage,
    ToolCallMessage,
    ToolResultMessage,
)
from ..domain.meta import Meta
from ..domain.repositories.chat_repo import ChatRepo
from ..domain.tool import ToolCall, ToolResult


_METADATA = MetaData()

_COMPANY = Table(
    "company",
    _METADATA,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

_OFFICE = Table(
    "office",
    _METADATA,
    Column("id", String, primary_key=True),
    Column("company_id", String, ForeignKey("company.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

_APP_USER = Table(
    "app_user",
    _METADATA,
    Column("id", String, primary_key=True),
    Column("company_id", String, ForeignKey("company.id"), nullable=False),
    Column("office_id", String, ForeignKey("office.id"), nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

_SYSTEM_PROMPT = Table(
    "system_prompt",
    _METADATA,
    Column("id", String, primary_key=True),
    Column("agent_id", String, nullable=False),
    Column("agent_version", String, nullable=False),
    Column("prompt_text", Text, nullable=False),
    Column("prompt_hash", String, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

_CONVERSATION = Table(
    "conversation",
    _METADATA,
    Column("id", String, primary_key=True),
    Column("user_id", String, ForeignKey("app_user.id"), nullable=False),
    Column("agent_id", String, nullable=False),
    Column("agent_version", String, nullable=False),
    Column("system_prompt_id", String, ForeignKey("system_prompt.id"), nullable=False),
    Column("title", String, nullable=True),
    Column("status", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
)

_MESSAGE_EVENT = Table(
    "message_event",
    _METADATA,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("message_uid", String, nullable=False, unique=True),
    Column("conversation_id", String, ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False),
    Column("seq", BigInteger, nullable=False),
    Column("role", String, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("request_id", String, nullable=True),
    Column(
        "response_to",
        String,
        ForeignKey("message_event.message_uid", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("meta", JSONB, nullable=True),
)

_MESSAGE_ITEM = Table(
    "message_item",
    _METADATA,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "message_id",
        BigInteger,
        ForeignKey("message_event.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("position", Integer, nullable=False),
    Column("item_type", String, nullable=False),
    Column("renderable", Boolean, nullable=False),
)

_MESSAGE_ITEM_TEXT = Table(
    "message_item_text",
    _METADATA,
    Column("item_id", BigInteger, ForeignKey("message_item.id", ondelete="CASCADE"), primary_key=True),
    Column("text", Text, nullable=False),
)

_MESSAGE_ITEM_FILE = Table(
    "message_item_file",
    _METADATA,
    Column("item_id", BigInteger, ForeignKey("message_item.id", ondelete="CASCADE"), primary_key=True),
    Column("source", String, nullable=False),
    Column("media_type", String, nullable=False),
    Column("uri", Text, nullable=False),
    Column("filename", String, nullable=False),
    Column("bytes", BigInteger, nullable=True),
)

_TOOL_CALL = Table(
    "tool_call",
    _METADATA,
    Column("item_id", BigInteger, ForeignKey("message_item.id", ondelete="CASCADE"), primary_key=True),
    Column("call_id", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("label", String, nullable=True),
    Column("args", JSONB, nullable=False),
)

_TOOL_RESULT = Table(
    "tool_result",
    _METADATA,
    Column("item_id", BigInteger, ForeignKey("message_item.id", ondelete="CASCADE"), primary_key=True),
    Column("call_id", String, ForeignKey("tool_call.call_id"), nullable=False),
    Column("status", String, nullable=False),
    Column("label", String, nullable=True),
    Column("result", JSONB, nullable=True),
    Column("error", JSONB, nullable=True),
)

_SCHEMA_READY = weakref.WeakKeyDictionary()
_SCHEMA_LOCK = threading.Lock()


def _ensure_schema(engine: Engine) -> None:
    if _SCHEMA_READY.get(engine):
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY.get(engine):
            return
        _METADATA.create_all(engine)
        _SCHEMA_READY[engine] = True


@event.listens_for(Engine, "engine_connect")
def _initialize_schema(connection, branch) -> None:
    if branch:
        return
    _ensure_schema(connection.engine)


class PostgresChatRepo(ChatRepo):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._metadata = _METADATA

        self._company = _COMPANY
        self._office = _OFFICE
        self._app_user = _APP_USER
        self._system_prompt = _SYSTEM_PROMPT
        self._conversation = _CONVERSATION
        self._message_event = _MESSAGE_EVENT
        self._message_item = _MESSAGE_ITEM
        self._message_item_text = _MESSAGE_ITEM_TEXT
        self._message_item_file = _MESSAGE_ITEM_FILE
        self._tool_call = _TOOL_CALL
        self._tool_result = _TOOL_RESULT

        _ensure_schema(self._engine)

    def load_chat(self, chat_id: str, user_id: str | None = None) -> Chat:
        with self._engine.begin() as connection:
            conversation_row = connection.execute(
                select(self._conversation).where(self._conversation.c.id == chat_id)
            ).one_or_none()

        if conversation_row is None:
            return Chat(chat_id, user_id=user_id)

        chat = Chat(
            chat_id,
            user_id=conversation_row.user_id,
            agent_id=conversation_row.agent_id,
            agent_version=conversation_row.agent_version,
            system_prompt_id=conversation_row.system_prompt_id,
            created_at=self._format_datetime(conversation_row.created_at),
            status=conversation_row.status,
            title=conversation_row.title,
            deleted_at=self._format_datetime(conversation_row.deleted_at) if conversation_row.deleted_at else None,
        )

        with self._engine.begin() as connection:
            message_rows = connection.execute(
                select(self._message_event)
                .where(self._message_event.c.conversation_id == chat_id)
                .order_by(self._message_event.c.seq)
            ).all()

            for message_row in message_rows:
                items = self._load_message_items(connection, message_row.id)
                message = Message(
                    type="message",
                    role=message_row.role,
                    created_at=self._format_datetime(message_row.created_at),
                    content=Content(items=items),
                    message_id=message_row.message_uid,
                    request_id=message_row.request_id,
                    response_to=message_row.response_to,
                    _meta=self._deserialize_meta(message_row.meta) if message_row.meta else None,
                )
                chat.add_message(message)

        return chat

    def save_chat(self, chat: Chat) -> None:
        if not chat.user_id:
            raise ValueError("Chat.user_id is required")
        if not chat.agent_id:
            raise ValueError("Chat.agent_id is required")
        if not chat.agent_version:
            raise ValueError("Chat.agent_version is required")
        if not chat.system_prompt_id:
            raise ValueError("Chat.system_prompt_id is required")

        now = datetime.now(timezone.utc)

        with self._engine.begin() as connection:
            existing = connection.execute(
                select(
                    self._conversation.c.created_at,
                    self._conversation.c.status,
                    self._conversation.c.title,
                    self._conversation.c.deleted_at,
                ).where(self._conversation.c.id == chat.id)
            ).one_or_none()
            existing_created_at = existing[0] if existing else None
            existing_status = existing[1] if existing else None
            existing_title = existing[2] if existing else None
            existing_deleted_at = existing[3] if existing else None

            created_at = (
                self._parse_datetime(chat.created_at)
                if chat.created_at
                else (existing_created_at or now)
            )
            status = chat.status or existing_status or "active"
            title = chat.title if chat.title is not None else existing_title
            deleted_at = (
                self._parse_datetime(chat.deleted_at)
                if chat.deleted_at
                else existing_deleted_at
            )

            connection.execute(
                pg_insert(self._conversation)
                .values(
                    id=chat.id,
                    user_id=chat.user_id,
                    agent_id=chat.agent_id,
                    agent_version=chat.agent_version,
                    system_prompt_id=chat.system_prompt_id,
                    title=title,
                    status=status,
                    created_at=created_at,
                    deleted_at=deleted_at,
                )
                .on_conflict_do_update(
                    index_elements=[self._conversation.c.id],
                    set_={
                        "user_id": chat.user_id,
                        "agent_id": chat.agent_id,
                        "agent_version": chat.agent_version,
                        "system_prompt_id": chat.system_prompt_id,
                        "title": title,
                        "status": status,
                        "deleted_at": deleted_at,
                    },
                )
            )

            connection.execute(
                delete(self._message_event).where(self._message_event.c.conversation_id == chat.id)
            )

            for seq, message in enumerate(chat.get_messages(), start=1):
                message_uid = message.message_id or str(uuid4())
                created_at = self._parse_datetime(message.created_at)
                meta_payload = asdict(message._meta) if message._meta else None

                message_event_id = connection.execute(
                    insert(self._message_event)
                    .values(
                        message_uid=message_uid,
                        conversation_id=chat.id,
                        seq=seq,
                        role=message.role,
                        created_at=created_at,
                        request_id=message.request_id,
                        response_to=message.response_to,
                        meta=meta_payload,
                    )
                    .returning(self._message_event.c.id)
                ).scalar_one()

                self._save_message_items(connection, message_event_id, message.content.items)

    def _save_message_items(
        self,
        connection,
        message_event_id: int,
        items: Iterable[Any],
    ) -> None:
        for position, item in enumerate(items, start=1):
            item_type, renderable = self._resolve_item_type(item)
            item_id = connection.execute(
                insert(self._message_item)
                .values(
                    message_id=message_event_id,
                    position=position,
                    item_type=item_type,
                    renderable=renderable,
                )
                .returning(self._message_item.c.id)
            ).scalar_one()

            if isinstance(item, TextMessage):
                connection.execute(
                    insert(self._message_item_text)
                    .values(item_id=item_id, text=item.data.text)
                )
                continue

            if isinstance(item, FileMessage):
                connection.execute(
                    insert(self._message_item_file)
                    .values(
                        item_id=item_id,
                        source=item.data.source,
                        media_type=item.data.media_type,
                        uri=item.data.uri,
                        filename=item.data.filename,
                        bytes=item.data.bytes,
                    )
                )
                continue

            if isinstance(item, ToolCallMessage):
                connection.execute(
                    insert(self._tool_call)
                    .values(
                        item_id=item_id,
                        call_id=item.data.call_id,
                        name=item.data.name,
                        label=item.data.label,
                        args=item.data.args,
                    )
                )
                continue

            if isinstance(item, ToolResultMessage):
                connection.execute(
                    insert(self._tool_result)
                    .values(
                        item_id=item_id,
                        call_id=item.data.call_id,
                        status=item.data.status,
                        label=item.data.label,
                        result=item.data.result,
                        error=item.data.error,
                    )
                )
                continue

            raise ValueError(f"Unsupported message item type: {type(item).__name__}")

    def _load_message_items(self, connection, message_event_id: int) -> list[Any]:
        items = []
        rows = connection.execute(
            select(self._message_item)
            .where(self._message_item.c.message_id == message_event_id)
            .order_by(self._message_item.c.position)
        ).all()

        for row in rows:
            item_type = row.item_type
            if item_type == "text":
                text_row = connection.execute(
                    select(self._message_item_text).where(
                        self._message_item_text.c.item_id == row.id
                    )
                ).one()
                items.append(
                    TextMessage(
                        type="text",
                        renderable=row.renderable,
                        data=TextContent(text=text_row.text),
                    )
                )
                continue

            if item_type == "file":
                file_row = connection.execute(
                    select(self._message_item_file).where(
                        self._message_item_file.c.item_id == row.id
                    )
                ).one()
                items.append(self._build_file_message(item_type, file_row, row.renderable))
                continue

            if item_type == "tool_call":
                call_row = connection.execute(
                    select(self._tool_call).where(self._tool_call.c.item_id == row.id)
                ).one()
                items.append(
                    ToolCallMessage(
                        type="tool_call",
                        renderable=row.renderable,
                        data=ToolCall(
                            call_id=call_row.call_id,
                            name=call_row.name,
                            args=call_row.args,
                            label=call_row.label,
                        ),
                    )
                )
                continue

            if item_type == "tool_result":
                result_row = connection.execute(
                    select(self._tool_result).where(self._tool_result.c.item_id == row.id)
                ).one()
                items.append(
                    ToolResultMessage(
                        type="tool_result",
                        renderable=row.renderable,
                        data=ToolResult(
                            call_id=result_row.call_id,
                            status=result_row.status,
                            result=result_row.result,
                            error=result_row.error,
                            label=result_row.label,
                        ),
                    )
                )
                continue

            raise ValueError(f"Unknown message item type: {item_type}")

        return items

    @staticmethod
    def _resolve_item_type(item: Any) -> tuple[str, bool]:
        if isinstance(item, TextMessage):
            return "text", item.renderable
        if isinstance(item, FileMessage):
            return "file", item.renderable
        if isinstance(item, ToolCallMessage):
            return "tool_call", item.renderable
        if isinstance(item, ToolResultMessage):
            return "tool_result", item.renderable
        raise ValueError(f"Unsupported message item type: {type(item).__name__}")

    @staticmethod
    def _build_file_message(item_type: str, row, renderable: bool) -> Message:
        return FileMessage(
            type="file",
            renderable=renderable,
            data=FileContent(
                source=row.source,
                media_type=row.media_type,
                uri=row.uri,
                filename=row.filename,
                bytes=row.bytes,
            ),
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)

    @staticmethod
    def _format_datetime(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat()

    def _deserialize_meta(self, payload: dict[str, Any]) -> Meta:
        timing = payload.get("timing_ms")
        tokens = payload.get("tokens")
        return Meta(
            client_msg_id=payload.get("client_msg_id"),
            request_id=payload.get("request_id"),
            trace_id=payload.get("trace_id"),
            model=payload.get("model"),
            agent_id=payload.get("agent_id"),
            agent_version=payload.get("agent_version"),
            system_prompt_id=payload.get("system_prompt_id"),
            timing_ms=self._deserialize_timing(timing) if timing else None,
            tokens=self._deserialize_tokens(tokens) if tokens else None,
        )

    @staticmethod
    def _deserialize_timing(payload: dict[str, Any]):
        from ..domain.timing_ms import TimingMs

        return TimingMs(
            total=payload.get("total"),
            llm=payload.get("llm"),
            db=payload.get("db"),
            cache=payload.get("cache"),
            upload=payload.get("upload"),
        )

    @staticmethod
    def _deserialize_tokens(payload: dict[str, Any]):
        from ..domain.token_counts import TokenCounts

        return TokenCounts(
            input=payload.get("input"),
            output=payload.get("output"),
        )
