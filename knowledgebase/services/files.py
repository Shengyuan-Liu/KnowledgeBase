"""File parsing, indexing and lifecycle management."""

from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.document_chunker import DocumentChunker
from knowledgebase.rag.parsing import DocumentParser, InvalidUploadError
from knowledgebase.schemas import File
from knowledgebase.storage.operations import (
    create_file,
    delete_chunks,
    delete_file_record,
    delete_pdf_source,
    get_file,
    get_files,
    get_pdf_revision,
    save_document_source,
    save_parent_child_chunks,
    save_pdf_source,
    update_file_status,
)
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.vectordb import ChromaStore


class OriginalUnavailableError(LookupError):
    """The requested ready PDF source is unavailable."""


class OriginalRevisionError(ValueError):
    """The retained PDF does not match the requested extraction revision."""


class FileService:
    """Own file transactions and shared parsing, embedding and storage resources."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: ChromaStore,
        *,
        embeddings: EmbeddingClient | None = None,
        assets: PdfAssets | None = None,
        parser: DocumentParser | None = None,
        chunker: DocumentChunker | None = None,
    ):
        self.sessions = sessions
        self.store = store
        self.embeddings = embeddings
        self.assets = assets
        self.parser = parser or DocumentParser()
        self.chunker = chunker or DocumentChunker(embeddings=embeddings)

    def _cleanup(self, file_id: str) -> None:
        self.store.delete_by_file_id(file_id)
        if self.assets is not None:
            self.assets.delete(file_id)
        with self.sessions.begin() as session:
            delete_chunks(session, file_id)
            delete_pdf_source(session, file_id)

    def list_files(self) -> list[File]:
        with self.sessions() as session:
            return get_files(session)

    def get_file(self, file_id: str) -> File | None:
        with self.sessions() as session:
            return get_file(session, file_id)

    def get_original(self, file_id: str, revision: str | None = None) -> tuple[File, Path]:
        with self.sessions() as session:
            file = get_file(session, file_id)
            current_revision = get_pdf_revision(session, file_id)
        if (
            file is None
            or file.status != "ready"
            or current_revision is None
            or self.assets is None
        ):
            raise OriginalUnavailableError("Original PDF is unavailable.")
        if revision is not None and revision != current_revision:
            raise OriginalRevisionError("This original does not match the saved extraction.")
        path = self.assets.path(file_id)
        if not path.is_file():
            raise OriginalUnavailableError("Original PDF is unavailable.")
        return file, path

    def recover(self) -> None:
        """Recover abandoned uploads while the caller exclusively owns the data directory."""
        with self.sessions() as session:
            interrupted = [file for file in get_files(session) if file.status == "processing"]
        for file in interrupted:
            with self.sessions.begin() as session:
                update_file_status(
                    session,
                    file.file_id,
                    "failed",
                    "Indexing was interrupted. Cleanup pending; delete this file to finish cleanup.",
                )
            try:
                self._cleanup(file.file_id)
                with self.sessions.begin() as session:
                    update_file_status(
                        session,
                        file.file_id,
                        "failed",
                        "Indexing was interrupted. Re-upload the original file and delete this failed record.",
                    )
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
                    save_document_source(
                        session, file.file_id, file.type, file.text, file.blocks, indexing=indexing
                    )
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
                    update_file_status(
                        session, file.file_id, "failed", f"{error} Cleanup pending: {cleanup_error}"
                    )
            raise
        return file.file_id

    def delete(self, file_id: str) -> None:
        """Exclude a file from retrieval before cleanup; retain failed deletions for retry."""
        with self.sessions.begin() as session:
            update_file_status(
                session,
                file_id,
                "failed",
                error_message="Deletion pending. Retry deletion to finish cleanup.",
            )
        self.store.delete_by_file_id(file_id)
        if self.assets is not None:
            self.assets.delete(file_id)
        with self.sessions.begin() as session:
            delete_chunks(session, file_id)
            delete_file_record(session, file_id)
