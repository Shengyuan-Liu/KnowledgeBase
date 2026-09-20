"""Generate text with the OpenAI Responses API."""

from openai import OpenAI
from openai.types.responses import EasyInputMessageParam


class LLMClient:
    """Use the chosen model; the caller owns the SDK client."""

    def __init__(self, client: OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def generate(self, messages: list[EasyInputMessageParam]) -> str:
        """Send messages unchanged and return the generated text."""
        response = self._client.responses.create(model=self._model, input=messages)
        return response.output_text
