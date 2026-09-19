"""Vector database integrations for storing and searching chunk vectors."""

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
        self,
        query_embedding: list[float],
        top_k: int = 5,
        file_ids: list[str] | None = None,
    ) -> list[VectorMatch]:
        """Return nearest chunks, optionally restricted to nonempty file_ids.

        None searches all files. Smaller raw distances are nearer.
        """
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances"],
            where={"file_id": {"$in": file_ids}} if file_ids is not None else None,
        )
        return [
            VectorMatch(chunk_id=chunk_id, distance=distance)
            for chunk_id, distance in zip(result["ids"][0], result["distances"][0])
        ]

    def delete_by_file_id(self, file_id: str) -> None:
        """Delete every vector associated with the given file."""
        self._collection.delete(where={"file_id": file_id})
