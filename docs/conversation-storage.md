# Conversation and Message Storage

This module stores conversation metadata and message text for later follow-up
resolution. The [conversation chat service](conversation-chat.md) connects these
helpers to follow-up resolution and the CLI.

## Records and snapshots

`knowledgebase/storage/models.py` defines these conversation tables:

| Table | Fields | Purpose |
| --- | --- | --- |
| `conversations` | `conversation_id`, `created_at` | Identify a conversation using a caller-supplied string ID |
| `messages` | `message_id`, `conversation_id`, `role`, `content`, `created_at` | Store user and assistant messages in append order |
| `answer_snapshots` | `message_id`, `retrieval_question`, `sources`, `citation_check` | Retain each completed assistant answer's evidence and diagnostics |

The database generates integer message IDs. IDs are global across conversations,
so gaps within one conversation are normal. Sorting by ID preserves append order
even when timestamps tie. Timestamps use naive UTC, consistent with file records.
Message content is preserved unchanged. The foreign key requires an existing
conversation, and a database check restricts roles to `user` and `assistant`.

`ConversationInfo` and `MessageInfo` in `knowledgebase/schemas.py` are Pydantic
snapshots: they remain usable after a session closes, and changing a snapshot does
not update a database record. Stored messages are conversation context, not factual
evidence for new answers.

Answer snapshots use the assistant message ID as a primary/foreign key. Sources
and citation diagnostics are JSON values. Historical file/chunk IDs inside sources
are not foreign keys to live records, so deleting source files retains past
excerpts. No existing message columns are changed.

## Operations and transaction ownership

The helpers in `knowledgebase/storage/operations.py` use the existing storage
convention: writes flush but do not commit; the caller owns commit and rollback.

| Operation | Result |
| --- | --- |
| `create_conversation(session, conversation_id)` | Insert metadata; duplicate IDs raise a database integrity error |
| `get_conversation(session, conversation_id)` | Return a `ConversationInfo`, or `None` if missing |
| `save_message(session, conversation_id, role, content)` | Append a message and return its `MessageInfo`, including the generated ID and timestamp |
| `get_messages(session, conversation_id, limit=None)` | Return all messages, or the latest positive number of messages, in oldest-to-newest append order |
| `save_answer_snapshot(session, message_id, retrieval_question, answer)` | Store an assistant answer's sources and diagnostics without committing |
| `get_conversation_detail(session, conversation_id)` | Return ordered display history and saved evidence, or `None` for an unknown conversation |

An empty or unknown conversation returns an empty message list. Use
`get_conversation` when distinguishing them matters. Limits count individual
messages, not complete user/assistant exchanges; a limited history may begin with
an assistant message. IDs and snapshots returned before commit do not guarantee
that the transaction will ultimately be saved.

## Usage

With an initialized session factory:

```python
from uuid import uuid4

from knowledgebase.storage.operations import (
    create_conversation,
    get_messages,
    save_message,
)

conversation_id = uuid4().hex
with session_factory.begin() as session:
    create_conversation(session, conversation_id)

# These texts stand in for an already completed question and answer.
with session_factory.begin() as session:
    save_message(session, conversation_id, "user", "What are the requirements?")
    save_message(session, conversation_id, "assistant", "The notes require 36 credits.")

with session_factory() as session:
    history = get_messages(session, conversation_id, limit=10)
```

`init_db` creates any missing tables, including `answer_snapshots`, when next
called. It retains data in existing file, chunk, conversation, and message tables.
Old messages have no snapshot, so their display details remain null; they are not
backfilled with new retrieval results. No existing table definitions changed.

## Scope and verification

The chat service saves completed exchanges and evidence in one transaction.
Streaming status is not stored. `get_messages` remains the text-only history used
for follow-up resolution. `get_conversation_detail` returns `ConversationDetail`
with saved evidence and a current `file_deleted` flag for each source. A missing
snapshot has null details; a recorded empty retrieval has an empty source list.
New answers must retrieve current evidence rather than reuse historical excerpts,
especially after deletion. See the [conversation API](conversation-api.md).

`tests/test_conversation_storage.py` uses real temporary SQLite databases to verify
persistence, timestamp/content preservation, equal-timestamp ordering, latest-N
selection, conversation isolation, detached snapshots, caller-controlled rollback,
atomic exchange writes, and initialization on an existing file database. Run the
full suite with `make test`; no model calls are needed for these storage tests.
