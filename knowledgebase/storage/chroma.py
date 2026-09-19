"""Store and search chunk vectors using an existing Chroma collection."""

from chromadb.api.models.Collection import Collection

from knowledgebase.schemas import Chunk, VectorMatch


class ChromaStore:
    """The caller creates the collection and chooses its distance metric."""

    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def upsert_chunks(
        self, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> None:
        """Insert or update vectors by chunk ID; keep canonical text in SQLite."""
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            metadatas=[{"file_id": chunk.file_id} for chunk in chunks],
        )

    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[VectorMatch]:
        """Return nearest chunks and raw distances; smaller distances are nearer."""
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances"],
        )
        return [
            VectorMatch(chunk_id=chunk_id, distance=distance)
            for chunk_id, distance in zip(result["ids"][0], result["distances"][0])
        ]

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete every vector associated with the given file."""
        self._collection.delete(where={"file_id": file_id})
