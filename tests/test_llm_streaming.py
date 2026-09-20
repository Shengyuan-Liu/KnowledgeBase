"""Exercise the real SDK stream parser with offline HTTP events."""

from contextlib import aclosing
import json

import anyio
import httpx2
from openai import AsyncOpenAI
import pytest

from knowledgebase.providers.llm import StreamingLLMClient


class EventBody(httpx2.AsyncByteStream):
    def __init__(self, terminal):
        self.terminal = terminal
        self.closed = False
        self.wait = None

    async def __aiter__(self):
        for text in ("  Café", " 🙂\n[1]"):
            event = {"type": "response.output_text.delta", "delta": text,
                     "item_id": "msg_1", "output_index": 0, "content_index": 0, "sequence_number": 1}
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode()
        if self.wait is not None:
            await self.wait.wait()
        if self.terminal is not None:
            event = {"type": self.terminal, "response": {"status": "completed"}, "sequence_number": 2}
            yield f"event: {self.terminal}\ndata: {json.dumps(event)}\n\n".encode()

    async def aclose(self):
        self.closed = True


def client(body, requests):
    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx2.Response(200, headers={"content-type": "text/event-stream"}, stream=body)

    return AsyncOpenAI(api_key="test-only-key", base_url="https://api.openai.test/v1",
                       http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handle)))


@pytest.mark.anyio
async def test_provider_yields_before_completion_and_closes():
    body = EventBody("response.completed")
    body.wait = anyio.Event()
    requests = []
    messages = [{"role": "user", "content": "Hours?"}]
    async with client(body, requests) as sdk:
        async with aclosing(StreamingLLMClient(sdk, "test-model").stream(messages)) as stream:
            assert await anext(stream) == "  Café"
            assert await anext(stream) == " 🙂\n[1]"
            assert not body.closed
            body.wait.set()
            with pytest.raises(StopAsyncIteration):
                await anext(stream)
    assert body.closed
    assert requests == [{"model": "test-model", "input": messages, "stream": True}]


@pytest.mark.anyio
@pytest.mark.parametrize("terminal", [None, "response.failed", "response.incomplete", "error"])
async def test_provider_never_treats_eof_or_failed_terminal_as_success(terminal):
    body = EventBody(terminal)
    async with client(body, []) as sdk:
        with pytest.raises(RuntimeError, match="stream"):
            async for _ in StreamingLLMClient(sdk, "test-model").stream([]):
                pass
    assert body.closed


@pytest.mark.anyio
async def test_cancelling_provider_wait_closes_upstream_connection():
    body = EventBody("response.completed")
    body.wait = anyio.Event()
    waiting = anyio.Event()
    async with client(body, []) as sdk:
        async def consume():
            async with aclosing(StreamingLLMClient(sdk, "test-model").stream([])) as stream:
                async for text in stream:
                    if text.endswith("[1]"):
                        waiting.set()

        async with anyio.create_task_group() as tasks:
            tasks.start_soon(consume)
            await waiting.wait()
            tasks.cancel_scope.cancel()
    assert body.closed
