"""File parsing, indexing and lifecycle management."""

from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.pdf_runtime import LocalPdfParser
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.vectordb import ChromaStore

from knowledgebase.config import Settings
from knowledgebase.rag.chunking import DocumentChunker
from knowledgebase.rag.parsing import DocumentParser, InvalidUploadError
from knowledgebase.storage.operations import (
    create_file, delete_chunks, delete_file_record, delete_pdf_source, get_files,
    save_document_source, save_parent_child_chunks, save_pdf_source,
    update_file_status,
)


class FileService:
    """Own file transactions and shared parsing, embedding and storage resources."""

    def __init__(
        self, sessions: sessionmaker[Session], store: ChromaStore, *,
        embeddings: EmbeddingClient | None = None, assets: PdfAssets | None = None,
        pdf_parser: LocalPdfParser | None = None, parser: DocumentParser | None = None, chunker: DocumentChunker | None = None,
    ):
        self.sessions = sessions
        self.store = store
        self.embeddings = embeddings
        self.assets = assets
        self.parser = parser or DocumentParser(pdf_parser)
        self.chunker = chunker or DocumentChunker(embeddings=embeddings)

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
                       semantic_batch_size=settings.semantic_batch_size, embedding_model=settings.embedding_model, embeddings=embeddings,
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
            batch, indexing = self.chunker.split(file)
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
