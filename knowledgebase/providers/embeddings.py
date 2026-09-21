"""Convert document text and queries into OpenAI embedding vectors."""

from openai import OpenAI

from knowledgebase.config import DEFAULT_EMBEDDING_MODEL


class EmbeddingClient:
    """Use one model for documents and queries; the caller owns the SDK client."""

    def __init__(
        self, client: OpenAI, model: str = DEFAULT_EMBEDDING_MODEL
    ) -> None:
        self._client = client
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed one batch and extract vectors in the provider's response order.

        Text is sent unchanged. SDK errors propagate to the caller.
        """
        response = self._client.embeddings.create(
            model=self._model, input=texts, encoding_format="float"
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        """Embed a question with the same model as documents."""
        return self.embed_documents([text])[0]
