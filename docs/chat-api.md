# Chat API

New source snapshots include optional one-based `start_line` and `end_line`
computed from the canonical document. Missing historical locations remain null.
The saved `retrieval` diagnostics also include optional `retrieval_seconds`
(retrieval plus source lookup) and `embedding_seconds`; existing rerank/packing
durations remain separate nested stages. These fields survive conversation
restoration and deletion. See the [frontend guide](frontend.md) for their display.

Start the local API with `make api`, using `OPENAI_API_KEY` in `.env`. File upload
and chat share the same SQLite database, Chroma collection, and embedding client.
The API uses `gpt-4.1` by default (`ANSWER_MODEL` in `.env`), retrieves up to five chunks, and uses up to ten recent
messages to resolve follow-ups, matching the current service defaults.

## Submit a question

`POST /api/chat` accepts JSON with a required nonblank `question` and an optional
`conversation_id`. Omit the ID or send `null` to start a new conversation. Supply
an existing ID to continue it. Original question text, including surrounding
whitespace, is preserved.

```bash
curl http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"When does the library close?"}'
```

After uploading a TXT file containing `The library closes at 5 PM.`, an illustrative
response is:

```json
{
  "answer": "The library closes at 5 PM. [1]",
  "sources": [
    {
      "source_id": 1,
      "file_id": "example-file-id",
      "file_name": "hours.txt",
      "chunk_id": "example-file-id:0",
      "text": "The library closes at 5 PM.",
      "distance": 0.12
    }
  ],
  "citation_check": {
    "valid_source_ids": [1],
    "invalid_source_ids": [],
    "no_citations": false
  },
  "conversation_id": "example-conversation-id",
  "message_id": 2,
  "question": "When does the library close?",
  "retrieval_question": "When does the library close?"
}
```

IDs, answer text, and distance above are examples. `message_id` identifies the saved
assistant message. Distances are cosine distances, not correctness probabilities.
Sources include all retrieved excerpts supplied to generation; a citation number
check does not assess factual support. See [citation checks](citations.md).

Use the returned conversation ID in the next request:

```json
{
  "question": "What time was that?",
  "conversation_id": "example-conversation-id"
}
```

History resolves references before fresh retrieval. It does not supply answer
evidence. An empty library returns `200` with an insufficient-evidence answer and
an empty source list, and saves that completed exchange.

## HTTP outcomes

| Status | Meaning |
| --- | --- |
| `200` | Complete JSON answer; the question and assistant answer have been saved |
| `404` | The supplied conversation does not exist |
| `422` | Invalid request, including a missing, empty, whitespace-only, or non-string question |
| `500` | Resolution, retrieval, generation, or persistence failed |

Processing failures return `{"detail":"Answer processing failed."}`. Failed turns
do not append a partial exchange or create a new conversation. Previously saved
history remains intact.

## Structure and boundaries

`api/chat.py` validates the HTTP contract and delegates to
`services/chat.answer_in_conversation`. Its synchronous handler accommodates the
existing blocking service. `api/app.py` constructs the LLM client at startup using
the same SDK client as embeddings, and closes that client on shutdown.

This endpoint waits for a complete answer and returns JSON. The separate
[streaming endpoint](chat-streaming.md), `POST /api/chat/stream`, returns SSE.
Source lists, citation diagnostics, and resolved questions are saved alongside
each completed assistant message in the same transaction. Restore them through the
[conversation reading API](conversation-api.md). Older messages without recorded
snapshots remain readable with null detail fields. Send turns for a given
conversation sequentially; concurrent turns are not coordinated.

## Verification

```bash
uv run --locked python -m pytest tests/test_chat_api.py tests/test_file_api.py
make test
```

Tests use temporary SQLite/Chroma storage and offline provider responses. They
cover upload-to-answer integration, continued conversations, saved original text,
source and citation fields, request validation, missing conversations, empty
retrieval, failure rollback, and the OpenAPI contract. They make no live API calls.

Model, retrieval and history defaults are configurable through `ANSWER_MODEL`,
`RESOLVER_MODEL`, `RETRIEVAL_TOP_K`, and `HISTORY_LIMIT`; see [runtime configuration](configuration.md).

## Parent evidence and retrieval diagnostics

With parent-child indexing, sources contain the complete expanded parent text,
its `parent_id`, matched child IDs, offsets, and structural metadata. Source numbers
refer to these final evidence regions. Completed answers include `retrieval`
diagnostics with candidate hits, budget exclusions, and evidence token counts;
SSE includes this field in `complete`. Source snapshots and diagnostics persist
in the same exchange transaction and survive source deletion. Older snapshots
have `retrieval: null`. See [parent-child retrieval](parent-child-retrieval.md)
for the full contract and evidence budget behavior.


## Automatic planned retrieval

An optional `retrieval_mode` field accepts `single` or `planned`, overriding the
configured `RETRIEVAL_MODE`. The default is `single`. Planned answers include
`retrieval.planning`, preserved in conversation history, with the validated plan,
execution trace, limits and exact supplied context. A deadline error returns HTTP
504; invalid/incomplete planner output returns the existing generic HTTP 500.
See [planned retrieval](planned-retrieval.md) for limits and provider requirements.
