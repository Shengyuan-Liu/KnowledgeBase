from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
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
