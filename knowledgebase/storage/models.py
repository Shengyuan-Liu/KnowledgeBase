from datetime import UTC, datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FileRecord(Base):
    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'ready', 'failed')", name="ck_files_status"
        ),
    )

    file_id: Mapped[str] = mapped_column(primary_key=True)
    file_name: Mapped[str]
    status: Mapped[str] = mapped_column(default="processing")
    error_message: Mapped[str | None] = mapped_column(Text)
    # Store naive UTC timestamps consistently, including after SQLite reads.
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class ChunkRecord(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("file_id", "index", name="uq_chunks_file_index"),
        CheckConstraint('"index" >= 0', name="ck_chunks_index"),
        CheckConstraint("start_offset >= 0", name="ck_chunks_start_offset"),
        CheckConstraint("end_offset > start_offset", name="ck_chunks_end_offset"),
    )

    chunk_id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.file_id"))
    text: Mapped[str] = mapped_column(Text)
    index: Mapped[int]
    start_offset: Mapped[int]
    end_offset: Mapped[int]


class DocumentSourceRecord(Base):
    """One canonical source and ordered parser output per v1 file."""

    __tablename__ = "document_sources"
    __table_args__ = (
        CheckConstraint("source_format IN ('txt', 'md')", name="ck_document_source_format"),
    )

    file_id: Mapped[str] = mapped_column(
        ForeignKey("files.file_id", ondelete="CASCADE"), primary_key=True,
    )
    source_format: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str]
    blocks: Mapped[list[dict]] = mapped_column(JSON)


class ChunkStructureRecord(Base):
    """Structural metadata supplements a canonical chunk without changing MVP columns."""

    __tablename__ = "chunk_structures"

    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"), primary_key=True,
    )
    heading_path: Mapped[list[str]] = mapped_column(JSON)
    source_block_indices: Mapped[list[int]] = mapped_column(JSON)
    token_count: Mapped[int]
    tokenizer: Mapped[str]
    max_tokens: Mapped[int]


class ParentChunkRecord(Base):
    """Canonical parent context stored independently of indexed child chunks."""

    __tablename__ = "parent_chunks"
    __table_args__ = (
        UniqueConstraint("file_id", "index", name="uq_parent_chunks_file_index"),
        CheckConstraint('"index" >= 0', name="ck_parent_chunks_index"),
        CheckConstraint("start_offset >= 0", name="ck_parent_chunks_start_offset"),
        CheckConstraint("end_offset > start_offset", name="ck_parent_chunks_end_offset"),
    )

    parent_id: Mapped[str] = mapped_column(primary_key=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.file_id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    index: Mapped[int]
    start_offset: Mapped[int]
    end_offset: Mapped[int]
    heading_path: Mapped[list[str]] = mapped_column(JSON)
    source_block_indices: Mapped[list[int]] = mapped_column(JSON)
    token_count: Mapped[int]
    tokenizer: Mapped[str]
    max_tokens: Mapped[int]


class ChildParentRecord(Base):
    """One parent association per structural child, without changing old chunk rows."""

    __tablename__ = "child_parents"

    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("chunk_structures.chunk_id", ondelete="CASCADE"), primary_key=True,
    )
    parent_id: Mapped[str] = mapped_column(ForeignKey("parent_chunks.parent_id"))


class ConversationRecord(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class MessageRecord(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_messages_role"),
    )

    # Database-assigned IDs preserve append order even when timestamps tie.
    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.conversation_id"), index=True
    )
    role: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class AnswerSnapshotRecord(Base):
    """Evidence as supplied to one answer, retained independently of live files."""

    __tablename__ = "answer_snapshots"

    message_id: Mapped[int] = mapped_column(ForeignKey("messages.message_id"), primary_key=True)
    retrieval_question: Mapped[str] = mapped_column(Text)
    # Source file/chunk IDs are historical values, not foreign keys to live data.
    sources: Mapped[list[dict]] = mapped_column(JSON)
    citation_check: Mapped[dict] = mapped_column(JSON)
