"""Immutable PDF extraction records, independent of storage and retrieval."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from knowledgebase.schemas import BlockType, SourceBlock


class FrozenRecord(BaseModel):
    model_config = ConfigDict(frozen=True)


class PdfPage(FrozenRecord):
    page_index: int
    width: float
    height: float
    printed_label: str | None = None


class PdfRegion(FrozenRecord):
    """End-exclusive canonical character range; box precision is explicit."""

    start_offset: int
    end_offset: int
    page_index: int
    bbox: tuple[float, float, float, float]
    precision: Literal["block", "cell", "table"]
    coordinate_system: Literal["top_left_pdf_points"] = "top_left_pdf_points"


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


class PdfWarning(FrozenRecord):
    code: str
    message: str
    page_indices: tuple[int, ...] = ()
    source_ref: str | None = None


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
