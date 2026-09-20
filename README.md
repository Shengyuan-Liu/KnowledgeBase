# KnowledgeBase

A TXT knowledge base with vector retrieval and source-grounded answers.

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

## Evaluation

Run the frozen NYU question set, grade answers with human review or an LLM judge, and
compare recorded experiments using the [evaluation guide](evals/README.md).
Every run retains questions, answers, retrieved evidence, settings, and scoring details.

## Tests

```bash
make test
```

To explicitly send one real generation request using `.env` credentials:

```bash
make test-live
```
