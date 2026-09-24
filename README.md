# KnowledgeBase

A TXT and Markdown knowledge base with structural chunking, hybrid retrieval,
and source-grounded answers.

The [v1 design documents](docs/v1/README.md) define the ongoing version.
TXT/Markdown parsing, structural chunking, and source storage are connected to
uploads. [Parent-child retrieval](docs/parent-child-retrieval.md) is the default
strategy.
[Hybrid retrieval](docs/hybrid-retrieval.md) is now the default: [BM25](docs/bm25.md)
and vector candidates are combined with [RRF](docs/rrf.md) before parent expansion.
`RETRIEVAL_STRATEGY=vector` retains the vector-only control.
Set `RERANK_ENABLED=true` to score a bounded fused-child window with the
[local BGE cross-encoder](docs/reranking.md) before top-k selection and parent expansion. API,
streaming chat, CLI, and evaluations share this path. Reranking defaults to off;
the vector-only control requires it to remain off.

## Run the local application

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
DATA_DIR=data/v1 make app
```

Open <http://127.0.0.1:8000>. This builds the React interface and serves it together
with the API from one local process. Upload a UTF-8 TXT or Markdown file, wait for Ready, ask a
question, and click its source citation to inspect the original text. Follow-up
questions share the current conversation; refresh restores completed messages.
Uploads and questions use real model APIs and incur provider charges.

The command explicitly selects `data/v1/`, even if an existing `.env` still selects
the MVP's `data/`. It reuses the same credentials and leaves that older library intact.
Local data persists under the selected directory. Stop with Ctrl+C or `make stop`; neither removes
saved data. On restart, interrupted uploads become Failed and their partial index
is cleaned. Re-upload the original file and delete the failed record. If cleanup is
still pending, Delete retries it. Ready files and completed conversations survive.
Only one API or CLI process may own the same data directory; use another `DATA_DIR`
for separate instances. The application is local and single-user, without authentication.

For frontend development, use `DATA_DIR=data/v1 make api` and `make frontend` in separate terminals,
then open <http://127.0.0.1:5173>. Do not run `make app` and `make api` concurrently
against the same data. See the [frontend guide](docs/frontend.md) for details.

## Interactive CLI

Run from the repository root with `OPENAI_API_KEY` in `.env`.

Index one or more UTF-8 TXT or Markdown files, then enter the question loop:

```bash
uv run python main.py --data-dir data/v1 notes.txt handbook.md
```

On subsequent runs, use the saved knowledge base:

```bash
uv run python main.py --data-dir data/v1
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
uv run python main.py --data-dir data/v1 --conversation-id <saved-conversation-id>
```

Original questions and completed answers are saved together. See the
[follow-up workflow](docs/conversation-chat.md) for service usage and boundaries.

Local data is stored under `DATA_DIR` (default `data/v1/`), with SQLite in
`knowledgebase.db` and Chroma in `chroma/`. The vector collection is `knowledgebase-chunks`.

All backend tuning lives in `.env`, with defaults in `knowledgebase/config.py` and a
complete template in `.env.example`. See the [configuration guide](docs/configuration.md)
for every setting and its precedence. The API, CLI and evaluation runner use the
same model, chunking and retrieval configuration.

Defaults are `gpt-4.1` for answers and follow-up resolution,
`text-embedding-3-small` for embeddings, children up to 512 tokens and parents up
to 1536 tokens counted with `cl100k_base`, no overlap, and top-k 5. The token budget is an experimental
starting point, not a measured quality improvement. Set `CHUNKING_STRATEGY=character`
to use the MVP splitter with `CHUNK_SIZE=2048` and `CHUNK_OVERLAP=256`.
The default `CHUNKING_STRATEGY=parent_child` indexes children and supplies deduplicated
parents as evidence. Set `CHUNKING_STRATEGY=structural` for the flat structural control. `EVIDENCE_MAX_TOKENS=4096` limits the
numbered evidence context for all strategies. Use a fresh `DATA_DIR` for comparisons;
these defaults have not been established as better through quality evaluation.
Set `RESOLVER_MODEL` to choose a separate follow-up model; blank follows
`ANSWER_MODEL`. Restart the application after changing `.env`.

Chunking changes affect new uploads only. Changing the embedding model requires
reindexing the original files into a new `DATA_DIR`; do not reuse incompatible
vectors. Existing files and conversation history remain in the previous directory.
Passing a file to the CLI again indexes a new copy. To reuse existing data, omit file paths.

Optional settings:

```bash
uv run python main.py --data-dir data/v1 --model gpt-4.1 --top-k 3
```

Indexing and answering with retrieved evidence make real OpenAI API calls.
Follow-up resolution adds one model call when conversation history is nonempty.
An empty knowledge base returns an insufficient-evidence answer with no chunks;
history-based resolution may still run, but answer generation does not.

## HTTP API

With `OPENAI_API_KEY` configured in `.env`, start the local API:

```bash
DATA_DIR=data/v1 make api
```

Open [interactive API documentation](http://127.0.0.1:8000/docs) after startup.
Upload, list, and delete TXT/Markdown files through `/api/files`. Upload waits for indexing
and returns `201` when ready. API and CLI share `DATA_DIR` from `.env` (default `data/v1`),
unless explicitly overridden as above.
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

See the [MVP release evaluation](evals/analyses/2026-09-21-mvp-release.md) for
verified functionality, real-provider results, all-case inspection and known answer
quality limitations of that historical baseline. The v1 structural pipeline has
offline integration coverage and a [targeted live Markdown acceptance report](evals/browser-runs/20260922T222123209Z-8d828f17/README.md).
Seven development questions passed direct evidence review; broader accuracy and
comparative retrieval quality were not measured in that Markdown-only check.
The later [paired hybrid comparison](evals/library-runs/20260923T221737Z-hybrid/README.md)
records 18 questions per mode against the active library, including both gains
and a prerequisite-question budget regression. The subsequent
[paired rerank comparison](evals/library-runs/20260924T000238Z-rerank/README.md)
records the original LLM scoring pipeline. The current
[dedicated BGE comparison](evals/library-runs/20260924T002009Z-bge-serialized/README.md)
records the local cross-encoder, a corrected MPS concurrency failure, and a CPT
evidence regression alongside the prerequisite improvement. The subsequent
[packing comparison](evals/library-runs/20260924T004817Z-child-first/README.md)
keeps admitted parents and uses remaining space for whole selected children; it
also records first-delta and full-completion latency over real HTTP streams.

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

To explicitly send one real generation request using the `.env` credentials and
`ANSWER_MODEL` (with the evaluation timeout/retry settings):

```bash
make test-live
```
