"""Generate text with the OpenAI Responses API."""

from collections.abc import AsyncGenerator
from copy import copy

import anyio
from openai import AsyncOpenAI, OpenAI
from openai.types.responses import EasyInputMessageParam
from knowledgebase.providers.limits import GenerationLimits


class LLMClient:
    """Use the chosen model; the caller owns the SDK client."""

    def __init__(self, client: OpenAI, model: str, *, reasoning_effort: str | None = None) -> None:
        self._client = client
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._limits: GenerationLimits | None = None

    def bounded(self, limits: GenerationLimits):
        bounded = copy(self)
        bounded._limits = limits
        return bounded

    def generate(self, messages: list[EasyInputMessageParam]) -> str:
        """Send messages unchanged and return the generated text."""
        options = {"reasoning": {"effort": self._reasoning_effort}} if self._reasoning_effort is not None else {}
        client = self._client
        if self._limits is not None:
            self._limits.check_input(messages)
            client = client.with_options(timeout=self._limits.remaining(), max_retries=0)
            options["max_output_tokens"] = self._limits.max_output_tokens
        response = client.responses.create(model=self._model, input=messages, **options)
        if self._limits is not None:
            self._limits.remaining()
            if response.status != "completed":
                raise RuntimeError("Model response did not complete successfully.")
        return response.output_text


class StreamingLLMClient:
    """Stream text with an async SDK client owned by the application."""

    def __init__(self, client: AsyncOpenAI, model: str, *, reasoning_effort: str | None = None) -> None:
        self._client = client
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._limits: GenerationLimits | None = None

    def bounded(self, limits: GenerationLimits):
        bounded = copy(self)
        bounded._limits = limits
        return bounded

    async def stream(self, messages: list[EasyInputMessageParam]) -> AsyncGenerator[str]:
        options = {"reasoning": {"effort": self._reasoning_effort}} if self._reasoning_effort is not None else {}
        client = self._client
        if self._limits is not None:
            self._limits.check_input(messages)
            client = client.with_options(timeout=self._limits.remaining(), max_retries=0)
            options["max_output_tokens"] = self._limits.max_output_tokens
            with anyio.fail_after(self._limits.remaining()):
                stream = await client.responses.create(model=self._model, input=messages, stream=True, **options)
        else:
            stream = await client.responses.create(model=self._model, input=messages, stream=True, **options)
        try:
            iterator = stream.__aiter__()
            while True:
                try:
                    if self._limits is not None:
                        with anyio.fail_after(self._limits.remaining()):
                            event = await anext(iterator)
                    else:
                        event = await anext(iterator)
                except StopAsyncIteration:
                    break
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
