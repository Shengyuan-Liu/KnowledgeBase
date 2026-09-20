"""Frame chat events and cancel generation when the HTTP client disconnects."""

from collections.abc import AsyncGenerator
from contextlib import aclosing
import json

import anyio
from fastapi.responses import StreamingResponse

from knowledgebase.schemas import ChatStreamEvent


def encode_sse(event: ChatStreamEvent) -> str:
    data = json.dumps({"request_id": event.request_id, **event.data}, ensure_ascii=False)
    return f"event: {event.event}\ndata: {data}\n\n"


class ChatStreamingResponse(StreamingResponse):
    """Listen for disconnects even while the provider is waiting for its next token."""

    media_type = "text/event-stream"

    def __init__(self, events: AsyncGenerator[ChatStreamEvent]):
        async def body():
            async with aclosing(events):
                async for event in events:
                    yield encode_sse(event)

        super().__init__(body(), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    async def __call__(self, scope, receive, send):
        try:
            async with anyio.create_task_group() as tasks:
                async def transmit():
                    try:
                        await self.stream_response(send)
                    except OSError:
                        pass  # A closed socket is also a client disconnect.
                    finally:
                        tasks.cancel_scope.cancel()

                tasks.start_soon(transmit)
                await self.listen_for_disconnect(receive)
                tasks.cancel_scope.cancel()
        finally:
            with anyio.CancelScope(shield=True):
                await self.body_iterator.aclose()
