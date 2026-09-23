# Streaming Chat API

`POST /api/chat/stream` returns incremental SSE events. The existing
[`POST /api/chat`](chat-api.md) continues to return complete JSON answers; the CLI
and evaluation runner keep their synchronous entry points.

Start the API with `make api`, upload a TXT file, then try:

```bash
curl -N http://127.0.0.1:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"When does the library close?","request_id":"question-1"}'
```

The body requires a nonblank `question` and `request_id`. Include a saved
`conversation_id` to continue a conversation, or omit it to start a new one.
Clients should generate a new request ID for each submission. Request IDs correlate
events; they are not persisted and do not provide retry deduplication.

## Events

The response uses `Content-Type: text/event-stream`, `Cache-Control: no-cache`,
and `X-Accel-Buffering: no`. Each frame has an `event` line and a JSON `data` line,
followed by a blank line. Every data object contains the submitted `request_id`.

| Event | Other data fields | Meaning |
| --- | --- | --- |
| `start` | `conversation_id` | Accepted; ID is null for a new conversation |
| `sources` | `sources` | Ordered excerpts supplied to generation, with source IDs, file/chunk IDs, names, text, and cosine distances |
| `answer_delta` | `delta` | Append this text exactly; multiple events may arrive |
| `debug` | `retrieval_question`, `distance_metric`, `elapsed_seconds` | Resolved query and time through generation/citation checking, excluding persistence |
| `complete` | All fields of `ConversationAnswer` | Final answer, sources, citation check, original/resolved question, and persisted conversation/message IDs |
| `error` | `message` | Processing failed after streaming began; no completion event follows |

Successful order is `start`, `sources`, text deltas, `debug`, then `complete`.
Failures during processing send `error` and end the stream. For example:

```text
event: answer_delta
data: {"request_id":"question-1","delta":"The library closes at 5 PM. [1]\n"}

```

Source numbers are local to each answer. Sources arrive before answer text, but
the final citation-number check appears in `complete`. Matching source numbers do
not establish factual support. A library with no eligible evidence returns the
standard insufficient-evidence text as one delta, then saves and completes without
answer-model calls. Follow-up resolution may still make its usual model call.

## Persistence, errors, and cancellation

The service uses the same retrieval, evidence prompt, citation checking, and
transactional persistence as the JSON endpoint. It saves the full question, answer,
and evidence only after the provider confirms successful completion. EOF without
provider completion, a failed/incomplete provider response, or a write failure
cannot produce a successful answer record. Database failures roll back the whole
exchange. Previously completed messages remain unchanged.

Blank/missing inputs return HTTP `422`, and an unknown conversation returns HTTP
`404`, before SSE starts. Setup failures return HTTP `500`. Failures after headers
have been sent remain HTTP `200` and use an SSE `error` with the public message
`Answer processing failed.`; internal provider or database errors are not included.

Disconnects during answer generation cancel the async provider stream and close
its HTTP connection. Synchronous resolution/retrieval run in worker threads; an
already running call may finish after cancellation, but its result will not advance
to answer generation or persistence. Cancellation before saving leaves no new turn.

The final short write transaction is shielded from cancellation. A disconnect after
that transaction starts may leave a **complete** saved answer whose `complete` event
never reaches the client. A missing completion event therefore means interrupted
delivery, not proof that nothing was saved. Reload a known conversation before
retrying; do not automatically replay the POST. A new conversation whose completion
was lost has no client-visible ID recovery endpoint yet.

Failed/interrupted partial text stays in the client's temporary UI state and is
not restored from the database. Send turns within a conversation sequentially;
concurrent writers are not coordinated.

## Frontend contract

Use a streamed `fetch` POST. Buffer fragmented SSE frames and decode UTF-8
incrementally: one network read is not necessarily one event. Match events to the
active `request_id`, ignore stale events, and use AbortController to cancel obsolete
requests. Before completion, temporary messages/sources belong to the request ID;
after completion, attach the returned conversation and assistant message IDs.
Reconcile displayed text with `complete.answer`. EOF without `complete` is an
interrupted response. Handle non-SSE HTTP errors separately.

## Implementation and verification

- `providers/llm.py`: `StreamingLLMClient` uses an application-owned `AsyncOpenAI`
  client and forwards actual text deltas; it requires `response.completed`.
- `rag/generation.py`: shares the grounded prompt with synchronous generation.
- `services/chat.py`: coordinates streaming and commits the same answer snapshot.
- `api/streaming.py`: frames events and listens for disconnects while the provider
  is waiting, including ASGI 2.4 connections.

The provider follows the official [OpenAI streaming guide](https://developers.openai.com/api/docs/guides/streaming-responses).
API startup owns and closes both sync and async SDK clients.

Run `make test`. Offline tests exercise the real SDK SSE parser, early text delivery,
provider completion/error/EOF handling, connection closure, follow-ups, empty
retrieval, HTTP errors, stream errors, atomic rollback, and history restoration.
The ASGI test pauses generation and verifies that HTTP text frames arrive before
the model finishes, then verifies disconnect cancellation. These tests do not call
live providers. The [frontend browser suite](frontend.md#verification) additionally
exercises real HTTP/SSE through the local Vite proxy with offline provider fixtures;
production proxy deployment remains unverified.

## Parent evidence and retrieval diagnostics

With parent-child indexing, sources contain the complete expanded parent text,
its `parent_id`, matched child IDs, offsets, and structural metadata. Source numbers
refer to these final evidence regions. Completed answers include `retrieval`
diagnostics with candidate hits, budget exclusions, and evidence token counts;
SSE includes this field in `complete`. Source snapshots and diagnostics persist
in the same exchange transaction and survive source deletion. Older snapshots
have `retrieval: null`. See [parent-child retrieval](parent-child-retrieval.md)
for the full contract and evidence budget behavior.
