"""Configure and compose the independent document chunking algorithms."""

from dataclasses import dataclass

from knowledgebase.defaults import (
    DEFAULT_CHUNK_MAX_TOKENS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_TOKENIZER,
    DEFAULT_CHUNKING_STRATEGY,
    DEFAULT_OVERLAP,
    DEFAULT_PARENT_MAX_TOKENS,
    DEFAULT_SEMANTIC_BATCH_SIZE,
    DEFAULT_SEMANTIC_SIMILARITY_THRESHOLD,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.chunking import split_parent_child, split_structured, split_text
from knowledgebase.rag.pdf_chunking import (
    PDF_PARENT_CONTEXT_VERSION,
    join_heading_parents,
)
from knowledgebase.rag.pdf_evidence import table_rows
from knowledgebase.rag.semantic_chunking import split_semantic
from knowledgebase.schemas import ChunkBatch, File


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

    embeddings: EmbeddingClient | None = None

    def split(self, file: File) -> tuple[ChunkBatch, dict]:
        strategy = "parent_child" if file.type == "pdf" else self.chunking_strategy
        semantic = None
        if strategy == "semantic":
            batch, semantic = split_semantic(
                file.text,
                file.blocks,
                file.file_id,
                self.embeddings.embed_documents,
                parent_max_tokens=self.parent_max_tokens,
                child_max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer,
                similarity_threshold=self.semantic_similarity_threshold,
                batch_size=self.semantic_batch_size,
            )
        elif strategy == "parent_child":
            batch = split_parent_child(
                file.text,
                file.blocks,
                file.file_id,
                parent_max_tokens=self.parent_max_tokens,
                child_max_tokens=self.chunk_max_tokens,
                encoding_name=self.chunk_tokenizer,
                table_row_spans=table_rows(file) if file.type == "pdf" else None,
            )
            if file.type == "pdf":
                batch = join_heading_parents(file, batch)
        elif strategy == "structural":
            batch = ChunkBatch(
                [],
                split_structured(
                    file.text,
                    file.blocks,
                    file.file_id,
                    max_tokens=self.chunk_max_tokens,
                    encoding_name=self.chunk_tokenizer,
                ),
            )
        elif strategy == "character":
            batch = ChunkBatch(
                [], split_text(file.text, file.file_id, self.chunk_size, self.overlap)
            )
        else:
            raise ValueError(
                "chunking_strategy must be structural, character, parent_child, or semantic."
            )
        indexing = {
            "strategy": strategy,
            "embedding_model": self.embedding_model,
            "chunk_max_tokens": self.chunk_max_tokens,
            "parent_max_tokens": self.parent_max_tokens,
            "tokenizer": self.chunk_tokenizer,
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "semantic": semantic,
        }
        if file.type == "pdf":
            indexing["pdf_parent_context"] = PDF_PARENT_CONTEXT_VERSION
        return batch, indexing
