"""Canonical source, chunk and PDF records shared by ingestion and retrieval."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class FileInfo(BaseModel):
    file_id: str
    file_name: str
    status: str
    error_message: str | None
    created_at: datetime
    page_count: int | None = None
    extraction_warnings: list[PdfWarning] = Field(default_factory=list)


class ChunkContent(BaseModel):
    """Canonical content shared by flat, child and parent chunks."""

    file_id: str
    text: str
    index: int
    start_offset: int
    end_offset: int


class Chunk(ChunkContent):
    chunk_id: str


class SourceBlock(BaseModel):
    """A structural block whose text is an exact slice of the original source."""

    kind: BlockType
    text: str
    start_offset: int
    end_offset: int
    heading_path: list[str]
    heading_level: int | None = None


class StructuredContent(ChunkContent):
    """Structural metadata shared by parents and retrieval-sized chunks."""

    heading_path: list[str]
    source_block_indices: list[int]
    token_count: int
    tokenizer: str
    max_tokens: int


class StructuredChunk(Chunk, StructuredContent):
    """A bounded source slice with its structure and token-counting settings."""


class ParentChunk(StructuredContent):
    """A bounded section region that supplies context for its child chunks."""

    parent_id: str


class ChildChunk(StructuredChunk):
    """A retrieval-sized source slice contained in exactly one parent."""

    parent_id: str


class ParentChildChunks(BaseModel):
    """Ordered parent and child snapshots, before persistence or indexing."""

    parents: list[ParentChunk]
    children: list[ChildChunk]


class DocumentSource(BaseModel):
    """Canonical document and parser output, independent of a database session."""

    file_id: str
    source_format: Literal["txt", "md", "pdf"]
    text: str
    source_hash: str
    blocks: list[SourceBlock]
    indexing: dict[str, Any] | None = None


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


class PdfBlock(FrozenRecord):
    source_ref: str
    kind: BlockType
    label: str
    text: str
    start_offset: int
    end_offset: int
    heading_path: tuple[str, ...]
    heading_level: int | None
    regions: tuple[PdfRegion, ...]
    table: PdfTable | None = None


class PdfParserIdentity(FrozenRecord):
    name: str = "docling"
    package_versions: tuple[tuple[str, str], ...]
    settings_json: str
    model_file_hashes: tuple[tuple[str, str], ...]


class PdfExtraction(FrozenRecord):
    schema_version: Literal[1] = 1
    source_hash: str
    extraction_hash: str
    revision_id: str
    text: str
    pages: tuple[PdfPage, ...]
    blocks: tuple[PdfBlock, ...]
    parser: PdfParserIdentity
    warnings: tuple[PdfWarning, ...]
    serialization: str = "Block separator: two newlines; table cells: tabs/newlines; separators are synthetic."

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def source_blocks(self) -> list[SourceBlock]:
        """Return independent copies for the existing structural chunker."""
        return [SourceBlock(
            kind=b.kind, text=b.text, start_offset=b.start_offset, end_offset=b.end_offset,
            heading_path=list(b.heading_path), heading_level=b.heading_level,
        ) for b in self.blocks]

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
