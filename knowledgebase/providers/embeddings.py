"""Convert document text and queries into OpenAI embedding vectors."""

from openai import OpenAI
from collections.abc import Callable
from copy import copy

from knowledgebase.defaults import DEFAULT_EMBEDDING_MODEL


class EmbeddingClient:
    """Use one model for documents and queries; the caller owns the SDK client."""

    def __init__(
        self, client: OpenAI, model: str = DEFAULT_EMBEDDING_MODEL
    ) -> None:
        self._client = client
        self._model = model
        self._remaining: Callable[[], float] | None = None

    def bounded(self, remaining: Callable[[], float]):
        bounded = copy(self)
        bounded._remaining = remaining
        return bounded

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed one batch and extract vectors in the provider's response order.

        Text is sent unchanged. SDK errors propagate to the caller.
        """
        client = self._client
        if self._remaining is not None:
            client = client.with_options(timeout=self._remaining(), max_retries=0)
        response = client.embeddings.create(
            model=self._model, input=texts, encoding_format="float"
        )
        if self._remaining is not None:
            self._remaining()
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        """Embed a question with the same model as documents."""
        return self.embed_documents([text])[0]
