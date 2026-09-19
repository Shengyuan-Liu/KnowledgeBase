"""Convert document text and queries into OpenAI embedding vectors."""

from math import isfinite

from openai import OpenAI


class EmbeddingClient:
    """Use one model for documents and queries; the caller owns the SDK client."""

    def __init__(
        self, client: OpenAI, model: str = "text-embedding-3-small"
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty.")
        self._client = client
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed one batch, returning vectors in the original input order.

        Empty batches return [] without calling OpenAI. Text is sent unchanged.
        The caller must keep batches within the provider's token limits; this
        method never truncates text. SDK errors propagate to the caller.
        """
        if not isinstance(texts, list) or any(
            not isinstance(text, str) for text in texts
        ):
            raise TypeError("texts must be a list of strings.")
        if not texts:
            return []
        if any(text == "" for text in texts):
            raise ValueError("texts must not contain empty strings.")
        if len(texts) > 2048:
            raise ValueError("A batch must not contain more than 2048 texts.")

        response = self._client.embeddings.create(
            model=self._model, input=texts, encoding_format="float"
        )
        if len(response.data) != len(texts):
            raise ValueError("Embedding count does not match input count.")

        ordered = sorted(response.data, key=lambda item: item.index)
        if [item.index for item in ordered] != list(range(len(texts))):
            raise ValueError("Embedding indices do not match input positions.")

        vectors = [item.embedding for item in ordered]
        dimension = len(vectors[0])
        if dimension == 0 or any(len(vector) != dimension for vector in vectors):
            raise ValueError("Embedding dimensions must be nonzero and consistent.")
        if any(not isfinite(value) for vector in vectors for value in vector):
            raise ValueError("Embedding values must be finite.")
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """Embed a question with the same model and validation as documents."""
        return self.embed_documents([text])[0]
