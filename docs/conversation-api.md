# Conversation Reading API

`GET /api/conversations/{conversation_id}` restores a saved conversation, including
the evidence recorded for each completed assistant answer. Start the API with
`make api` and use the conversation ID returned by [chat](chat-api.md).

```bash
curl http://127.0.0.1:8000/api/conversations/<conversation-id>
```

## Response

The endpoint returns `200` with `conversation_id`, `created_at`, and `messages`
ordered by ascending `message_id`. An existing empty conversation has
`messages: []`. An unknown ID returns `404` with
`{"detail":"Conversation not found."}`.

Every message contains its ID, conversation ID, role, original content, creation
time, and three nullable detail fields:

| Field | Completed assistant answer | User or legacy message without a snapshot |
| --- | --- | --- |
| `retrieval_question` | Question used for retrieval, including follow-up resolution | `null` |
| `sources` | Ordered source snapshots with current deletion flags | `null` |
| `citation_check` | Original source-number diagnostics | `null` |

An illustrative assistant message is:

```json
{
  "message_id": 2,
  "conversation_id": "example-conversation-id",
  "role": "assistant",
  "content": "The library closes at 5 PM. [1]",
  "created_at": "2026-09-20T12:00:00",
  "retrieval_question": "When does the library close?",
  "sources": [{
    "source_id": 1,
    "file_id": "example-file-id",
    "file_name": "hours.txt",
    "chunk_id": "example-file-id:0",
    "text": "The library closes at 5 PM.",
    "distance": 0.12,
    "file_deleted": false
  }],
  "citation_check": {
    "valid_source_ids": [1],
    "invalid_source_ids": [],
    "no_citations": false
  }
}
```

Values above are examples. Timestamps are naive UTC, matching existing message
storage. Citation numbers are local to an answer: identify an excerpt using both
`message_id` and `source_id`. All excerpts supplied to generation are retained,
including ones the answer did not cite. Distances are not correctness probabilities,
and citation-number checks do not establish factual support.

## Missing evidence and deleted files

`sources: null` means no snapshot was recorded. `sources: []` means a completed
answer was recorded with no retrieved evidence. Legacy answers are never re-run,
re-retrieved, or assigned reconstructed sources during reading.

Each historical source includes `file_deleted`, computed from whether its original
file record currently exists. Once file deletion completes, the flag is `true`;
the original filename, excerpt, chunk ID, distance, and citation checks stay intact.
An existing file in a failed state is not marked deleted. This flag describes
deletion only, not retrieval eligibility. A UI can display `Source deleted` while
still showing the historical excerpt.

Reading a conversation makes no embedding or generation calls. These snapshots
serve historical display only. Follow-up resolution continues to load message
text, and new answers retrieve current ready-file evidence. Deleting a file removes
it from new retrieval even though old source cards remain readable.

## Persistence and compatibility

The chat service stores the question, answer, and answer snapshot in one
transaction. Snapshot failures roll back the whole exchange, including a newly
created conversation. CLI conversations use the same service and also record
snapshots. Stateless evaluation answers do not create conversation records.

The new `answer_snapshots` table uses the assistant message ID as its primary and
foreign key. Source lists and citation diagnostics are JSON snapshots; their file
and chunk IDs are historical values without foreign keys to live source records.
`init_db` creates the new table on startup without changing existing tables or
discarding data. Existing messages remain readable with null detail fields.

The endpoint returns the entire known conversation. Conversation listing and
pagination are not implemented. The [streaming chat endpoint](chat-streaming.md)
also saves completed exchanges here; interrupted partial text is not stored.

## Verification

`tests/test_answer_snapshots.py` covers storage round trips, message/source
association, conversation isolation, caller-owned rollback, and initialization on
an older database. `tests/test_chat_api.py` covers restoration after application
restart, missing/empty/legacy conversations, deletion followed by a fresh question,
and complete rollback when snapshot persistence fails. Tests use offline model
responses and temporary SQLite/Chroma storage. Run `make test` for the full suite.
