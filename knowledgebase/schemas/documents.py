"""Canonical source, chunk and PDF records shared by ingestion and retrieval."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


BlockType = Literal[
    "heading", "paragraph", "list", "code", "table", "blockquote",
    "thematic_break", "reference",
]


class FrozenRecord(BaseModel):
    model_config = ConfigDict(frozen=True)


class PdfRegion(FrozenRecord):
    start_offset: int
    end_offset: int
    page_index: int
    bbox: tuple[float, float, float, float]
    precision: Literal["block", "cell", "table"]
    coordinate_system: Literal["top_left_pdf_points"] = "top_left_pdf_points"


class PdfWarning(FrozenRecord):
    code: str
    message: str
    page_indices: tuple[int, ...] = ()
    source_ref: str | None = None


class PdfSupplement(BaseModel):
    """Separately located source text, never spliced into a canonical chunk."""
    role: Literal["column_header", "row_header", "caption", "note", "preceding_text"]
    table_id: str
    text: str
    start_offset: int
    end_offset: int
    regions: list[PdfRegion]


class PdfTableSpan(BaseModel):
    table_id: str
    # [row start, row end, column start, column end, character start, character end]
    cells: list[tuple[int, int, int, int, int, int]]
    column_header_spans: list[tuple[int, int]] = Field(default_factory=list)
    # Derived reading aid; original coordinates and canonical excerpts remain authoritative.
    reading: str | None = None


class PdfEvidence(BaseModel):
    revision_id: str
    source_hash: str
    page_count: int
    regions: list[PdfRegion]
    tables: list[PdfTableSpan] = Field(default_factory=list)
    supplements: list[PdfSupplement] = Field(default_factory=list)
    warnings: list[PdfWarning] = Field(default_factory=list)


class Chunk(BaseModel):
    """One canonical span; type distinguishes flat, parent and child roles."""

    chunk_id: str
    file_id: str
    text: str
    index: int
    start_offset: int
    end_offset: int
    type: Literal["flat", "parent", "child"] = "flat"
    parent_id: str | None = None
    heading_path: list[str] = Field(default_factory=list)
    source_block_indices: list[int] = Field(default_factory=list)
    token_count: int | None = None
    tokenizer: str | None = None
    max_tokens: int | None = None


@dataclass
class ChunkBatch:
    """A split result groups two lists of the same Chunk model."""

    parents: list[Chunk]
    children: list[Chunk]


class PdfPage(FrozenRecord):
    page_index: int
    width: float
    height: float
    printed_label: str | None = None


class PdfCell(FrozenRecord):
    text: str
    start_offset: int
    end_offset: int
    row_start: int
    row_end: int
    column_start: int
    column_end: int
    column_header: bool
    row_header: bool
    row_section: bool
    regions: tuple[PdfRegion, ...]


class PdfTable(FrozenRecord):
    table_id: str
    rows: int
    columns: int
    cells: tuple[PdfCell, ...]
    caption_refs: tuple[str, ...]
    note_refs: tuple[str, ...]


class SourceBlock(FrozenRecord):
    """An exact source slice, with optional PDF location and table data."""

    kind: BlockType
    text: str
    start_offset: int
    end_offset: int
    heading_path: tuple[str, ...] = ()
    heading_level: int | None = None
    source_ref: str | None = None
    label: str | None = None
    regions: tuple[PdfRegion, ...] = ()
    table: PdfTable | None = None


class PdfParserIdentity(FrozenRecord):
    name: str = "docling"
    package_versions: tuple[tuple[str, str], ...]
    settings_json: str
    model_file_hashes: tuple[tuple[str, str], ...]


class File(FrozenRecord):
    """A file snapshot shared by parsing, storage and the API.

    Metadata-only reads leave content empty. PDF geometry is optional; type is
    the single dispatch field for parsing and indexing.
    """

    type: Literal["txt", "md", "pdf"]
    file_id: str = ""
    file_name: str = ""
    status: str = "processing"
    error_message: str | None = None
    created_at: datetime | None = None
    text: str = ""
    source_hash: str = ""
    blocks: tuple[SourceBlock, ...] = ()
    indexing: dict[str, Any] | None = None
    page_count: int | None = None
    pages: tuple[PdfPage, ...] = ()
    warnings: tuple[PdfWarning, ...] = Field(default=(), serialization_alias="extraction_warnings")
    parser: PdfParserIdentity | None = None
    schema_version: Literal[1] = 1
    extraction_hash: str | None = None
    revision_id: str | None = None
    serialization: str = "Block separator: two newlines; table cells: tabs/newlines; separators are synthetic."

    @model_validator(mode="after")
    def page_metadata(self):
        # Frozen pre-unification PDF records store pages but no page_count field.
        if self.type == "pdf" and self.page_count is None:
            object.__setattr__(self, "page_count", len(self.pages))
        return self

    def extraction_data(self) -> dict:
        """Keep the established PDF revision payload independent of file metadata."""
        return self.model_dump(mode="json", include={
            "schema_version", "source_hash", "extraction_hash", "revision_id", "text",
            "pages", "blocks", "parser", "warnings", "serialization",
        })

    def locate(self, start: int, end: int) -> tuple[PdfRegion, ...]:
        """Find all intersecting page regions without inventing smaller boxes."""
        if not 0 <= start <= end <= len(self.text):
            raise ValueError("Span must lie within the canonical extracted text.")
        if start == end:
            return ()
        return tuple(r.model_copy(update={
            "start_offset": max(start, r.start_offset), "end_offset": min(end, r.end_offset),
        }) for b in self.blocks for r in b.regions
            if r.start_offset < end and start < r.end_offset)
