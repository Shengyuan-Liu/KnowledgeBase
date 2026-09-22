"""Ingest and delete TXT/Markdown content across SQLite and the vector database."""

from pathlib import Path
from typing import Literal
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.config import (
    DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, DEFAULT_CHUNKING_STRATEGY,
    DEFAULT_CHUNK_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER,
)
from knowledgebase.rag.chunking import split_structured, split_text
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.storage.operations import (
    create_file,
    delete_chunks,
    delete_file_record,
    get_files,
    save_chunks,
    save_document_source,
    update_file_status,
)
from knowledgebase.storage.vectordb import ChromaStore


class InvalidUploadError(ValueError):
    """The supplied file is not nonempty UTF-8 TXT/Markdown content."""


def recover_interrupted_files(
    session_factory: sessionmaker[Session], vector_store: ChromaStore,
) -> None:
    """Recover abandoned uploads while the caller exclusively owns the data directory."""
    with session_factory() as session:
        interrupted = [file for file in get_files(session) if file.status == "processing"]
    for file in interrupted:
        # Commit eligibility first so interrupted cleanup remains safe and deletable.
        with session_factory.begin() as session:
            update_file_status(session, file.file_id, "failed",
                               "Indexing was interrupted. Cleanup pending; delete this file to finish cleanup.")
        try:
            vector_store.delete_by_file_id(file.file_id)
            with session_factory.begin() as session:
                delete_chunks(session, file.file_id)
                update_file_status(session, file.file_id, "failed",
                                   "Indexing was interrupted. Re-upload the original file and delete this failed record.")
        except Exception:
            # The retained failed record exposes cleanup failure and supports normal deletion retry.
            continue


def ingest_file(
    file_name: str,
    content: bytes,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    *,
    chunking_strategy: Literal["structural", "character"] = DEFAULT_CHUNKING_STRATEGY,
    chunk_max_tokens: int = DEFAULT_CHUNK_MAX_TOKENS,
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER,
) -> str:
    """Index a UTF-8 TXT/Markdown file and return its generated file ID.

    This service owns its transactions. Original text is retained in SQLite
    with ordered parser blocks and chunks. Processing errors propagate
    after marking the file failed and cleaning up its vectors.
    """
    suffix = Path(file_name).suffix.lower()
    if suffix not in (".txt", ".md"):
        raise InvalidUploadError("Only .txt and .md files are supported.")
    source_format = "md" if suffix == ".md" else "txt"
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidUploadError("The file must be UTF-8 encoded.") from error
    if not text.strip():
        raise InvalidUploadError("The file must contain nonempty text.")

    file_id = uuid4().hex
    with session_factory.begin() as session:
        create_file(session, file_id, file_name)

    try:
        blocks = parse_markdown(text) if source_format == "md" else parse_txt(text)
        if chunking_strategy == "structural":
            chunks = split_structured(
                text, blocks, file_id, max_tokens=chunk_max_tokens, encoding_name=chunk_tokenizer,
            )
        elif chunking_strategy == "character":
            chunks = split_text(text, file_id, chunk_size=chunk_size, overlap=overlap)
        else:
            raise ValueError("chunking_strategy must be structural or character.")
        embeddings = embedding_client.embed_documents([chunk.text for chunk in chunks])
        with session_factory.begin() as session:
            save_document_source(session, file_id, source_format, text, blocks)
            save_chunks(session, chunks)
            vector_store.upsert_chunks(chunks, embeddings)
            update_file_status(session, file_id, "ready")
    except Exception as error:
        with session_factory.begin() as session:
            update_file_status(session, file_id, "failed", error_message=str(error))
        vector_store.delete_by_file_id(file_id)
        raise

    return file_id


def delete_file(
    file_id: str,
    session_factory: sessionmaker[Session],
    vector_store: ChromaStore,
) -> None:
    """Exclude a file from new retrievals, then remove its vectors and records.

    Commit the non-ready state before touching Chroma. If either cleanup step
    fails, propagate the error and retain the failed file for another explicit
    deletion attempt. Chunk and file deletion share a SQLite transaction.
    A missing file raises FileRecordNotFoundError before touching the vector store.
    """
    with session_factory.begin() as session:
        update_file_status(
            session, file_id, "failed",
            error_message="Deletion pending. Retry deletion to finish cleanup.",
        )

    vector_store.delete_by_file_id(file_id)

    with session_factory.begin() as session:
        delete_chunks(session, file_id)
        delete_file_record(session, file_id)
