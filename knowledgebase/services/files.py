"""Ingest and delete TXT/Markdown/PDF sources, assets and search indexes."""

from pathlib import Path
from typing import Literal
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.config import (
    DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP, DEFAULT_CHUNKING_STRATEGY,
    DEFAULT_CHUNK_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER, DEFAULT_PARENT_MAX_TOKENS,
    DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD, DEFAULT_SEMANTIC_BATCH_SIZE,
)
from knowledgebase.rag.chunking import split_parent_child, split_structured, split_text
from knowledgebase.rag.parsing import parse_markdown, parse_txt
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.rag.pdf_chunking import PDF_PARENT_CONTEXT_VERSION, join_heading_parents
from knowledgebase.storage.operations import (
    create_file,
    delete_chunks,
    delete_file_record,
    get_files,
    save_chunks,
    save_document_source,
    save_parent_child_chunks,
    update_file_status,
)
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.services.pdf import LocalPdfParser
from knowledgebase.storage.operations import save_pdf_source, delete_pdf_source


class InvalidUploadError(ValueError):
    """The supplied file has an unsupported format or no supported content."""


def recover_interrupted_files(
    session_factory: sessionmaker[Session], vector_store: ChromaStore,
    *, assets: PdfAssets | None = None,
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
            if assets is not None:
                assets.delete(file.file_id)
            with session_factory.begin() as session:
                delete_chunks(session, file.file_id)
                delete_pdf_source(session, file.file_id)
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
    chunking_strategy: Literal["structural", "character", "parent_child", "semantic"] = DEFAULT_CHUNKING_STRATEGY,
    chunk_max_tokens: int = DEFAULT_CHUNK_MAX_TOKENS,
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER,
    parent_max_tokens: int = DEFAULT_PARENT_MAX_TOKENS,
    semantic_similarity_threshold: float = DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD,
    semantic_batch_size: int = DEFAULT_SEMANTIC_BATCH_SIZE,
    embedding_model: str | None = None,
    assets: PdfAssets | None = None,
    pdf_parser: LocalPdfParser | None = None,
) -> str:
    """Index a TXT/Markdown/PDF file and return its generated file ID.

    This service owns its transactions. Original text is retained in SQLite
    with ordered parser blocks and chunks. Processing errors propagate
    after marking the file failed and cleaning up its vectors.
    """
    suffix = Path(file_name).suffix.lower()
    if suffix not in (".txt", ".md", ".pdf"):
        raise InvalidUploadError("Only .txt, .md and .pdf files are supported.")
    source_format = suffix[1:]
    text = ""
    if source_format == "pdf":
        if not content.startswith(b"%PDF-"):
            raise InvalidUploadError("The file must be a PDF document.")
        if assets is None or pdf_parser is None:
            raise InvalidUploadError("PDF storage and parser are not configured.")
    else:
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
        extraction = None
        if source_format == "pdf":
            assets.save(file_id, content)
            extraction = pdf_parser.parse(content)
            text = extraction.text
            if not text.strip():
                raise InvalidUploadError("No supported text was extracted. OCR is disabled; scanned-only PDFs are not supported.")
            blocks = extraction.source_blocks()
            chunking_strategy = "parent_child"
        else:
            blocks = parse_markdown(text) if source_format == "md" else parse_txt(text)
        hierarchy = None
        semantic = None
        if chunking_strategy == "semantic":
            from knowledgebase.rag.semantic_chunking import split_semantic

            hierarchy, semantic = split_semantic(
                text, blocks, file_id, embedding_client.embed_documents,
                parent_max_tokens=parent_max_tokens, child_max_tokens=chunk_max_tokens,
                encoding_name=chunk_tokenizer, similarity_threshold=semantic_similarity_threshold,
                batch_size=semantic_batch_size,
            )
            chunks = hierarchy.children
        elif chunking_strategy == "parent_child":
            hierarchy = split_parent_child(
                text, blocks, file_id, parent_max_tokens=parent_max_tokens,
                child_max_tokens=chunk_max_tokens, encoding_name=chunk_tokenizer,
                table_row_spans=table_rows(extraction) if extraction is not None else None,
            )
            if extraction is not None:
                hierarchy = join_heading_parents(extraction, hierarchy)
            chunks = hierarchy.children
        elif chunking_strategy == "structural":
            chunks = split_structured(
                text, blocks, file_id, max_tokens=chunk_max_tokens, encoding_name=chunk_tokenizer,
            )
        elif chunking_strategy == "character":
            chunks = split_text(text, file_id, chunk_size=chunk_size, overlap=overlap)
        else:
            raise ValueError("chunking_strategy must be structural, character, parent_child, or semantic.")
        embeddings = embedding_client.embed_documents([chunk.text for chunk in chunks])
        with session_factory.begin() as session:
            indexing = {
                "strategy": chunking_strategy, "embedding_model": embedding_model,
                "chunk_max_tokens": chunk_max_tokens, "parent_max_tokens": parent_max_tokens,
                "tokenizer": chunk_tokenizer, "chunk_size": chunk_size, "overlap": overlap,
                "semantic": semantic,
            }
            if extraction is not None:
                indexing["pdf_parent_context"] = PDF_PARENT_CONTEXT_VERSION
                save_pdf_source(session, file_id, extraction, indexing)
            else:
                save_document_source(session, file_id, source_format, text, blocks, indexing=indexing)
            if hierarchy is not None:
                save_parent_child_chunks(session, hierarchy)
            else:
                save_chunks(session, chunks)
            vector_store.upsert_chunks(chunks, embeddings)
            update_file_status(session, file_id, "ready")
    except Exception as error:
        with session_factory.begin() as session:
            update_file_status(session, file_id, "failed", error_message=str(error))
        try:
            vector_store.delete_by_file_id(file_id)
            if assets is not None:
                assets.delete(file_id)
            with session_factory.begin() as session:
                delete_chunks(session, file_id)
                delete_pdf_source(session, file_id)
        except Exception as cleanup_error:
            with session_factory.begin() as session:
                update_file_status(session, file_id, "failed", f"{error} Cleanup pending: {cleanup_error}")
        raise

    return file_id


def delete_file(
    file_id: str,
    session_factory: sessionmaker[Session],
    vector_store: ChromaStore,
    *, assets: PdfAssets | None = None,
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
    if assets is not None:
        assets.delete(file_id)

    with session_factory.begin() as session:
        delete_chunks(session, file_id)
        delete_file_record(session, file_id)
