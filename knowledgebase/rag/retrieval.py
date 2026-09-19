"""Retrieve canonical chunk text from ready files."""

from sqlalchemy.orm import Session

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.schemas import RetrievedChunk
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.operations import get_chunks_by_ids, get_files


def retrieve(
    question: str,
    session: Session,
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Search ready files and load their original text in vector-search order.

    No ready files means no evidence and no embedding request. The caller owns
    the database session and model client; this function does not commit.
    """
    ready_file_ids = [
        file.file_id for file in get_files(session) if file.status == "ready"
    ]
    if not ready_file_ids:
        return []

    query_embedding = embedding_client.embed_query(question)
    matches = vector_store.search(
        query_embedding, top_k=top_k, file_ids=ready_file_ids
    )
    chunks = get_chunks_by_ids(session, [match.chunk_id for match in matches])
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    return [
        RetrievedChunk(chunk=chunks_by_id[match.chunk_id], distance=match.distance)
        for match in matches
    ]
