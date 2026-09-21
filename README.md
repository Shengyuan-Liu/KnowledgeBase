# KnowledgeBase

A TXT knowledge base with vector retrieval and source-grounded answers.

## Run the local MVP

Requirements: macOS or Linux, Python 3.13+, uv, and a Node.js version supported by
the locked frontend dependencies (Node 22.12+). Run commands from this directory.

```bash
uv sync --locked
npm --prefix frontend ci
# Create the local configuration only if it does not already exist.
test -f .env || cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then start the complete application:

```bash
make app
```

Open <http://127.0.0.1:8000>. This builds the React interface and serves it together
with the API from one local process. Upload a UTF-8 TXT file, wait for Ready, ask a
question, and click its source citation to inspect the original text. Follow-up
questions share the current conversation; refresh restores completed messages.
Uploads and questions use real model APIs and incur provider charges.

Local data persists under `data/`. Stop with Ctrl+C or `make stop`; neither removes
saved data. On restart, interrupted uploads become Failed and their partial index
is cleaned. Re-upload the original TXT and delete the failed record. If cleanup is
still pending, Delete retries it. Ready files and completed conversations survive.
Only one API or CLI process may own the same data directory; use another `DATA_DIR`
for separate instances. The MVP is local and single-user, without authentication.

For frontend development, use `make api` and `make frontend` in separate terminals,
then open <http://127.0.0.1:5173>. Do not run `make app` and `make api` concurrently
against the same data. See the [frontend guide](docs/frontend.md) for details.

## Interactive CLI

Run from the repository root with `OPENAI_API_KEY` in `.env`.

Index one or more UTF-8 TXT files, then enter the question loop:

```bash
uv run python main.py notes.txt handbook.txt
```

On subsequent runs, use the saved knowledge base:

```bash
uv run python main.py
```

Each question prints an answer and the retrieved chunks with source numbers,
filenames, and chunk IDs. The list includes all excerpts supplied to the model,
including excerpts it did not cite. Questions in one CLI invocation share a saved
conversation. Recent history resolves follow-up references before fresh retrieval;
old messages are not supplied as answer evidence. The CLI prints the conversation
ID and, when it changes, the question used for retrieval. Type `exit` or `quit` to
leave, or press Ctrl+D or Ctrl+C at the question prompt. Blank input is ignored.

Each answer also shows a [citation number check](docs/citations.md): valid source
IDs, invalid IDs, or no numbered citations. This locates references; it does not
judge whether an excerpt supports a claim, and it leaves the answer unchanged.

Each invocation starts a new conversation unless you resume a printed ID from the
same data directory:

```bash
uv run python main.py --conversation-id <saved-conversation-id>
```

Original questions and completed answers are saved together. See the
[follow-up workflow](docs/conversation-chat.md) for service usage and boundaries.

Local data is stored in `data/knowledgebase.db` and `data/chroma/`, using the
`knowledgebase-chunks` collection. The default embedding model is
`text-embedding-3-small`; the default answer model is `gpt-4.1-nano`.
Passing a file again indexes a new copy. To reuse existing data, omit file paths.

Optional settings:

```bash
uv run python main.py --data-dir data --model gpt-4.1-nano --top-k 3
```

Indexing and answering with retrieved evidence make real OpenAI API calls.
Follow-up resolution adds one model call when conversation history is nonempty.
An empty knowledge base returns an insufficient-evidence answer with no chunks;
history-based resolution may still run, but answer generation does not.

## HTTP API

With `OPENAI_API_KEY` configured in `.env`, start the local API:

```bash
make api
```

Open [interactive API documentation](http://127.0.0.1:8000/docs) after startup.
Upload, list, and delete TXT files through `/api/files`. Upload waits for indexing
and returns `201` when ready. API and CLI share `DATA_DIR` from `.env` (default `data`).
See the [file API guide](docs/file-api.md) for requests and error codes.

Submit questions to `POST /api/chat` with a JSON `question` and an optional
`conversation_id` to continue a saved conversation. The endpoint returns the full
answer, retrieved sources, citation diagnostics, and saved conversation/message IDs
as JSON after processing completes. See the [chat API guide](docs/chat-api.md) for
examples and error codes. Restore saved messages and their original evidence with
`GET /api/conversations/{conversation_id}`; see the
[conversation API guide](docs/conversation-api.md). For incremental text, use
`POST /api/chat/stream` with an additional `request_id`; see the
[streaming guide](docs/chat-streaming.md) for events, completion, and cancellation.

## Evaluation

Run the frozen NYU question set, grade answers with human review or an LLM judge, and
compare recorded experiments using the [evaluation guide](evals/README.md).
Every run retains questions, answers, retrieved evidence, settings, and scoring details.

## Development dependencies

Notebook tools are optional. Install them with `uv sync --group notebooks` when
needed; API, CLI, evaluation, and tests do not require Jupyter.

## Tests

```bash
make test
```

To explicitly send one real generation request using `.env` credentials:

```bash
make test-live
```
