"""File parsing, indexing and lifecycle management."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.services.pdf import LocalPdfParser
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.vectordb import ChromaStore

from knowledgebase.config import (
    Settings, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, DEFAULT_CHUNKING_STRATEGY,
    DEFAULT_CHUNK_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER, DEFAULT_PARENT_MAX_TOKENS,
    DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD, DEFAULT_SEMANTIC_BATCH_SIZE,
)
from knowledgebase.rag.chunking import split_parent_child, split_structured, split_text
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.rag.pdf_chunking import PDF_PARENT_CONTEXT_VERSION, join_heading_parents
from knowledgebase.schemas import ChunkBatch, File
from knowledgebase.storage.operations import (
    create_file, delete_chunks, delete_file_record, delete_pdf_source, get_files,
    save_document_source, save_parent_child_chunks, save_pdf_source,
    update_file_status,
)


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
                raise InvalidUploadError("No supported text was extracted. OCR is disabled; scanned-only PDFs are not supported.")
            return parsed.model_copy(update={"file_id": file.file_id, "file_name": file.file_name})
        blocks = parse_markdown(file.text) if file.type == "md" else parse_txt(file.text)
        return file.model_copy(update={"blocks": tuple(blocks),
                                       "source_hash": sha256(content).hexdigest()})


@dataclass
class DocumentChunker:
    """Own indexing settings and dispatch to the source-preserving split algorithms."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    overlap: int = DEFAULT_OVERLAP
    chunking_strategy: str = DEFAULT_CHUNKING_STRATEGY
    chunk_max_tokens: int = DEFAULT_CHUNK_MAX_TOKENS
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER
    parent_max_tokens: int = DEFAULT_PARENT_MAX_TOKENS
    semantic_similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD
    semantic_batch_size: int = DEFAULT_SEMANTIC_BATCH_SIZE
    embedding_model: str | None = None

    def split(self, file: File, embeddings: EmbeddingClient) -> tuple[ChunkBatch, dict]:
        strategy = "parent_child" if file.type == "pdf" else self.chunking_strategy
        semantic = None
        if strategy == "semantic":
            from knowledgebase.rag.semantic_chunking import split_semantic

            batch, semantic = split_semantic(
                file.text, file.blocks, file.file_id, embeddings.embed_documents,
                parent_max_tokens=self.parent_max_tokens, child_max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer, similarity_threshold=self.semantic_similarity_threshold,
                batch_size=self.semantic_batch_size,
            )
        elif strategy == "parent_child":
            batch = split_parent_child(
                file.text, file.blocks, file.file_id, parent_max_tokens=self.parent_max_tokens,
                child_max_tokens=self.chunk_max_tokens, encoding_name=self.chunk_tokenizer,
                table_row_spans=table_rows(file) if file.type == "pdf" else None,
            )
            if file.type == "pdf":
                batch = join_heading_parents(file, batch)
        elif strategy == "structural":
            batch = ChunkBatch([], split_structured(
                file.text, file.blocks, file.file_id, max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer,
            ))
        elif strategy == "character":
            batch = ChunkBatch([], split_text(file.text, file.file_id, self.chunk_size, self.overlap))
        else:
            raise ValueError("chunking_strategy must be structural, character, parent_child, or semantic.")
        indexing = {
            "strategy": strategy, "embedding_model": self.embedding_model,
            "chunk_max_tokens": self.chunk_max_tokens, "parent_max_tokens": self.parent_max_tokens,
            "tokenizer": self.chunk_tokenizer, "chunk_size": self.chunk_size, "overlap": self.overlap,
            "semantic": semantic,
        }
        if file.type == "pdf":
            indexing["pdf_parent_context"] = PDF_PARENT_CONTEXT_VERSION
        return batch, indexing


class FileService:
    """Own file transactions and shared parsing, embedding and storage resources."""

    def __init__(
        self, sessions: sessionmaker[Session], store: ChromaStore, *,
        embeddings: EmbeddingClient | None = None, assets: PdfAssets | None = None,
        pdf_parser: LocalPdfParser | None = None, chunker: DocumentChunker | None = None,
    ):
        self.sessions = sessions
        self.store = store
        self.embeddings = embeddings
        self.assets = assets
        self.parser = DocumentParser(pdf_parser)
        self.chunker = chunker or DocumentChunker()

    @classmethod
    def from_settings(
        cls, settings: Settings, sessions: sessionmaker[Session], embeddings: EmbeddingClient,
        store: ChromaStore, *, assets: PdfAssets | None = None, pdf_parser: LocalPdfParser | None = None,
    ) -> Self:
        return cls(sessions, store, embeddings=embeddings, assets=assets, pdf_parser=pdf_parser,
                   chunker=DocumentChunker(
                       chunk_size=settings.chunk_size, overlap=settings.chunk_overlap,
                       chunking_strategy=settings.chunking_strategy, chunk_max_tokens=settings.chunk_max_tokens,
                       chunk_tokenizer=settings.chunk_tokenizer, parent_max_tokens=settings.parent_max_tokens,
                       semantic_similarity_threshold=settings.semantic_similarity_threshold,
                       semantic_batch_size=settings.semantic_batch_size, embedding_model=settings.embedding_model,
                   ))

    def _cleanup(self, file_id: str) -> None:
        self.store.delete_by_file_id(file_id)
        if self.assets is not None:
            self.assets.delete(file_id)
        with self.sessions.begin() as session:
            delete_chunks(session, file_id)
            delete_pdf_source(session, file_id)

    def recover(self) -> None:
        """Recover abandoned uploads while the caller exclusively owns the data directory."""
        with self.sessions() as session:
            interrupted = [file for file in get_files(session) if file.status == "processing"]
        for file in interrupted:
            with self.sessions.begin() as session:
                update_file_status(session, file.file_id, "failed",
                                   "Indexing was interrupted. Cleanup pending; delete this file to finish cleanup.")
            try:
                self._cleanup(file.file_id)
                with self.sessions.begin() as session:
                    update_file_status(session, file.file_id, "failed",
                                       "Indexing was interrupted. Re-upload the original file and delete this failed record.")
            except Exception:
                # Retain failed records so normal deletion can retry unfinished cleanup.
                continue

    def ingest(self, name: str, content: bytes) -> str:
        file = self.parser.prepare(name, content)
        if file.type == "pdf" and (self.assets is None or self.parser.pdf_parser is None):
            raise InvalidUploadError("PDF storage and parser are not configured.")
        with self.sessions.begin() as session:
            create_file(session, file.file_id, file.file_name)
        try:
            if file.type == "pdf":
                self.assets.save(file.file_id, content)
            file = self.parser.parse(file, content)
            batch, indexing = self.chunker.split(file, self.embeddings)
            vectors = self.embeddings.embed_documents([chunk.text for chunk in batch.children])
            with self.sessions.begin() as session:
                if file.type == "pdf":
                    save_pdf_source(session, file.file_id, file, indexing)
                else:
                    save_document_source(session, file.file_id, file.type, file.text, file.blocks, indexing=indexing)
                save_parent_child_chunks(session, batch)
                self.store.upsert_chunks(batch.children, vectors)
                update_file_status(session, file.file_id, "ready")
        except Exception as error:
            with self.sessions.begin() as session:
                update_file_status(session, file.file_id, "failed", error_message=str(error))
            try:
                self._cleanup(file.file_id)
            except Exception as cleanup_error:
                with self.sessions.begin() as session:
                    update_file_status(session, file.file_id, "failed", f"{error} Cleanup pending: {cleanup_error}")
            raise
        return file.file_id

    def delete(self, file_id: str) -> None:
        """Exclude a file from retrieval before cleanup; retain failed deletions for retry."""
        with self.sessions.begin() as session:
            update_file_status(session, file_id, "failed",
                               error_message="Deletion pending. Retry deletion to finish cleanup.")
        self.store.delete_by_file_id(file_id)
        if self.assets is not None:
            self.assets.delete(file_id)
        with self.sessions.begin() as session:
            delete_chunks(session, file_id)
            delete_file_record(session, file_id)
