"""Parse document structure without rewriting the canonical source text."""

import re
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from markdown_it import MarkdownIt

from knowledgebase.rag.pdf_runtime import LocalPdfParser
from knowledgebase.schemas import BlockType, File, SourceBlock

_MARKDOWN = MarkdownIt("commonmark", {"html": False, "inline_definitions": True}).enable("table")

_BLOCK_TYPES: dict[str, BlockType] = {
    "heading_open": "heading",
    "paragraph_open": "paragraph",
    "bullet_list_open": "list",
    "ordered_list_open": "list",
    "fence": "code",
    "code_block": "code",
    "table_open": "table",
    "blockquote_open": "blockquote",
    "hr": "thematic_break",
    "definition": "reference",
}


def _line_offsets(text: str) -> list[int]:
    """Map parser line boundaries to original Python character offsets."""
    return [0, *(match.end() for match in re.finditer(r"\r\n|\r|\n", text)), len(text)]


def parse_txt(text: str) -> list[SourceBlock]:
    """Group nonblank lines into paragraphs, without interpreting Markdown."""
    offsets = _line_offsets(text)
    blocks: list[SourceBlock] = []
    paragraph_start: int | None = None
    paragraph_end = 0
    for start, end in zip(offsets, offsets[1:]):
        if text[start:end].strip():
            if paragraph_start is None:
                paragraph_start = start
            paragraph_end = end
        elif paragraph_start is not None:
            blocks.append(
                SourceBlock(
                    kind="paragraph",
                    text=text[paragraph_start:paragraph_end],
                    start_offset=paragraph_start,
                    end_offset=paragraph_end,
                    heading_path=[],
                )
            )
            paragraph_start = None
    if paragraph_start is not None:
        blocks.append(
            SourceBlock(
                kind="paragraph",
                text=text[paragraph_start:paragraph_end],
                start_offset=paragraph_start,
                end_offset=paragraph_end,
                heading_path=[],
            )
        )
    return blocks


def parse_markdown(text: str) -> list[SourceBlock]:
    """Return nonoverlapping top-level blocks with their enclosing heading path.

    Lists and blockquotes retain their nested content as one source region.
    Heading labels retain inline Markdown; they are metadata, not quoted text.
    Blank separators remain in the source but do not produce standalone blocks.
    """
    offsets = _line_offsets(text)
    tokens = _MARKDOWN.parse(text)
    headings: list[tuple[int, str]] = []
    blocks: list[SourceBlock] = []
    for index, token in enumerate(tokens):
        if token.level != 0 or token.map is None:
            continue
        level = None
        if token.type == "heading_open":
            level = int(token.tag[1:])
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, tokens[index + 1].content))
        start, end = (offsets[line] for line in token.map)
        blocks.append(
            SourceBlock(
                kind=_BLOCK_TYPES[token.type],
                text=text[start:end],
                start_offset=start,
                end_offset=end,
                heading_path=[title for _, title in headings],
                heading_level=level,
            )
        )
    return blocks


class InvalidUploadError(ValueError):
    """The supplied file has an unsupported format or no supported content."""


class DocumentParser:
    """Select a parser from File.type and return the same file with parsed content."""

    def __init__(self, pdf_parser: LocalPdfParser | None = None):
        self.pdf_parser = pdf_parser

    def prepare(self, name: str, content: bytes) -> File:
        file_type = Path(name).suffix.lower().lstrip(".")
        if file_type not in ("txt", "md", "pdf"):
            raise InvalidUploadError("Only .txt, .md and .pdf files are supported.")
        file = File(type=file_type, file_id=uuid4().hex, file_name=name)
        if file.type == "pdf":
            if not content.startswith(b"%PDF-"):
                raise InvalidUploadError("The file must be a PDF document.")
        else:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise InvalidUploadError("The file must be UTF-8 encoded.") from error
            if not text.strip():
                raise InvalidUploadError("The file must contain nonempty text.")
            file = file.model_copy(update={"text": text})
        return file

    def parse(self, file: File, content: bytes) -> File:
        if file.type == "pdf":
            parsed = self.pdf_parser.parse(content)
            if not parsed.text.strip():
                raise InvalidUploadError(
                    "No supported text was extracted. OCR is disabled; scanned-only PDFs are not supported."
                )
            return parsed.model_copy(update={"file_id": file.file_id, "file_name": file.file_name})
        blocks = parse_markdown(file.text) if file.type == "md" else parse_txt(file.text)
        return file.model_copy(
            update={"blocks": tuple(blocks), "source_hash": sha256(content).hexdigest()}
        )
