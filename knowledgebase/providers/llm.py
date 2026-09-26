"""Generate text with the OpenAI Responses API."""

from collections.abc import AsyncGenerator

import anyio
from openai import AsyncOpenAI, OpenAI
from openai.types.responses import EasyInputMessageParam


class LLMClient:
    """Use the chosen model; the caller owns the SDK client."""

    def __init__(self, client: OpenAI, model: str, *, reasoning_effort: str | None = None) -> None:
        self._client = client
        self._model = model
        self._reasoning_effort = reasoning_effort

    def generate(self, messages: list[EasyInputMessageParam]) -> str:
        """Send messages unchanged and return the generated text."""
        options = {"reasoning": {"effort": self._reasoning_effort}} if self._reasoning_effort is not None else {}
        response = self._client.responses.create(model=self._model, input=messages, **options)
        return response.output_text


class StreamingLLMClient:
    """Stream text with an async SDK client owned by the application."""

    def __init__(self, client: AsyncOpenAI, model: str, *, reasoning_effort: str | None = None) -> None:
        self._client = client
        self._model = model
        self._reasoning_effort = reasoning_effort

    async def stream(self, messages: list[EasyInputMessageParam]) -> AsyncGenerator[str]:
        options = {"reasoning": {"effort": self._reasoning_effort}} if self._reasoning_effort is not None else {}
        stream = await self._client.responses.create(model=self._model, input=messages, stream=True, **options)
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
