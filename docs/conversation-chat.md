# Follow-Up Resolution and Conversation Chat

`knowledgebase/rag/query.py` provides `resolve_question(question, history, llm_client)`.
With no history it returns the original question unchanged and makes no model call.
With history it uses one call to rewrite the current question into a standalone
retrieval question. For example, after discussing NYU MSDS, "How many credits does
it require?" can become "How many credits does NYU MSDS require?"

The prompt preserves user intent, names, years, and semesters. It asks the model
to keep standalone questions unchanged and preserve ambiguous references instead
of inventing a subject. History is sent as ordered role/content data, not as new
system instructions. These are model instructions, not guarantees of semantic
correctness; inspect the returned retrieval question when diagnosing a bad answer.
There are no repair calls or automatic retries at this layer.

## Conversation service

`answer_in_conversation` in `knowledgebase/services/chat.py` coordinates:

1. Load the latest `history_limit` messages from the supplied conversation, oldest
   to newest. The default is 10 individual messages. An unknown ID raises
   `LookupError` before model calls. Omit the ID to start a fresh conversation.
2. Resolve the question after closing the history read session.
3. Call the existing `answer_question` with the resolved question. Retrieval uses
   current ready files, and generation receives only that question and retrieved
   excerpts. Old answers are not injected into the generation prompt as evidence.
4. In one write transaction, create the conversation if new and save the original
   user question, completed assistant answer, and its evidence snapshot. Return
   only after commit.

Resolution, retrieval, or generation failures do not append messages. If saving
fails, the complete exchange rolls back. Failed/interrupted turns are not yet stored
as separate records. Calls for a single conversation are sequential; this service
does not coordinate concurrent writers or stream responses.

The returned `ConversationAnswer` includes `answer`, `sources`, `citation_check`, `conversation_id`,
the assistant's `message_id`, original `question`, and `retrieval_question`. Original
message text is persisted; the resolved question, source list, and
[citation diagnostics](citations.md) are stored in `answer_snapshots`, linked to
the assistant message. The [conversation reading API](conversation-api.md) restores
these details without retrieving new evidence. The original answer stays unchanged.

With configured clients and a session factory:

```python
from knowledgebase.services.chat import answer_in_conversation

first = answer_in_conversation(
    "What is NYU MSDS?", session_factory, embedding_client, vector_store, llm_client,
)
followup = answer_in_conversation(
    "How many credits does it require?",
    session_factory, embedding_client, vector_store, llm_client,
    conversation_id=first.conversation_id,
)
print(followup.retrieval_question)
print(followup.answer)
```

`answer_question` remains stateless for independent callers and the fixed single-turn
evaluation runner. It neither reads nor saves conversations. This keeps existing
evaluation cases isolated rather than carrying context from one case into another.

## CLI behavior

Run `uv run python main.py` for a new conversation using the existing local knowledge
base. Questions within that invocation share the returned conversation ID. Resume
with `uv run python main.py --conversation-id <id>` using the same `--data-dir`.
The CLI prints the ID after successful turns, plus a retrieval question when it
differs from the original. It does not reprint old messages on resumption.

The same LLM client/model handles resolution and answer generation. With nonempty
history, one resolution request is added even when the question is already standalone.
When no ready files remain after deletion, a follow-up may still call the resolver,
but it returns the standard insufficient-evidence answer with no answer-generation
call. Remembering an old answer does not make deleted excerpts eligible evidence.

## Verification

`tests/test_query.py`, `tests/test_chat.py`, and `tests/test_cli.py` cover no-history
behavior, ordered resolution input, embedding/generation using the resolved question,
original-message persistence, history limits, conversation isolation, deletion before
a follow-up, failed-turn rollback, and CLI resumption. Storage and vector retrieval
use real temporary SQLite/Chroma databases; model responses are offline doubles.
These tests verify the integration contract, not real-model pronoun-resolution
accuracy. Run all checks with `make test`.
