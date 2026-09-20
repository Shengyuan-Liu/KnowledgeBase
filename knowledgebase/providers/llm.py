"""Generate text with the OpenAI Responses API."""

from collections.abc import AsyncGenerator

import anyio
from openai import AsyncOpenAI, OpenAI
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


class StreamingLLMClient:
    """Stream text with an async SDK client owned by the application."""

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def stream(self, messages: list[EasyInputMessageParam]) -> AsyncGenerator[str]:
        stream = await self._client.responses.create(model=self._model, input=messages, stream=True)
        try:
            async for event in stream:
                if event.type == "response.output_text.delta":
                    yield event.delta
                elif event.type == "response.completed":
                    return
                elif event.type in {"response.failed", "response.incomplete", "error"}:
                    raise RuntimeError("Model stream did not complete successfully.")
            raise RuntimeError("Model stream ended without completion.")
        finally:
            # Cancellation must still release the upstream HTTP connection.
            with anyio.CancelScope(shield=True):
                await stream.close()
