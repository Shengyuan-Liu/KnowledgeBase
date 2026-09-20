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
including excerpts it did not cite. Questions are independent; previous turns
are not included in the prompt. Type `exit` or `quit` to leave, or press Ctrl+D
or Ctrl+C at the question prompt. Blank input is ignored.

Local data is stored in `data/knowledgebase.db` and `data/chroma/`, using the
`knowledgebase-chunks` collection. The default embedding model is
`text-embedding-3-small`; the default answer model is `gpt-4.1-nano`.
Passing a file again indexes a new copy. To reuse existing data, omit file paths.

Optional settings:

```bash
uv run python main.py --data-dir data --model gpt-4.1-nano --top-k 3
```

Indexing and answering with retrieved evidence make real OpenAI API calls.
An empty knowledge base returns an insufficient-evidence answer with no chunks.

## Tests

```bash
make test
```

To explicitly send one real generation request using `.env` credentials:

```bash
make test-live
```
