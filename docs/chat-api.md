# Chat API

Start the local API with `make api`, using `OPENAI_API_KEY` in `.env`. File upload
and chat share the same SQLite database, Chroma collection, and embedding client.
The API uses `gpt-4.1-nano`, retrieves up to five chunks, and uses up to ten recent
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

This endpoint currently waits for a complete answer and returns JSON. SSE in the
[frontend design](mvp/mvp-frontend-design.md#api-and-stream-contract) remains a future
step. Source lists, citation diagnostics, and resolved questions are saved alongside
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
