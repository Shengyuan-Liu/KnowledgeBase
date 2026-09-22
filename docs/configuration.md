# Runtime configuration

Edit the ignored root `.env` to change local runtime settings. The complete template is
[.env.example](../.env.example); all Python defaults are centralized in
[knowledgebase/config.py](../knowledgebase/config.py).

Settings are read when the API starts, when the CLI launches, or when an evaluation
run/model-grade command starts. Restart the application after editing `.env`.
Configuration is not reloaded in the middle of a conversation or an upload.

## Available settings

| Variable | Default | Used by |
| --- | --- | --- |
| `OPENAI_API_KEY` | Required | Provider authentication; never commit it |
| `OPENAI_BASE_URL` | Blank: SDK default endpoint | API, CLI, model evaluations, and live smoke test |
| `OPENAI_TIMEOUT_SECONDS` | `600` | API/CLI provider request timeout in seconds |
| `OPENAI_MAX_RETRIES` | `2` | API/CLI SDK retry limit |
| `DATA_DIR` | `data/v1` | Application storage; isolated evaluation indexes live under `<DATA_DIR>/evals/<run-id>` |
| `ANSWER_MODEL` | `gpt-4.1` | JSON/streamed answers, CLI, evaluation generation, live smoke test |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Both document and query embeddings in every entry point |
| `RESOLVER_MODEL` | Blank: use `ANSWER_MODEL` | Follow-up question rewriting in API and CLI |
| `CHUNKING_STRATEGY` | `structural` | `structural` or the MVP `character` baseline, for new uploads |
| `CHUNK_MAX_TOKENS` | `512` | Structural chunk token limit; experimental starting value |
| `CHUNK_TOKENIZER` | `cl100k_base` | tiktoken encoding used to count structural chunk tokens |
| `CHUNK_SIZE` | `2048` | Maximum characters per chunk in `character` mode only |
| `CHUNK_OVERLAP` | `256` | Character overlap in `character` mode only |
| `RETRIEVAL_TOP_K` | `5` | Maximum retrieved evidence chunks per question |
| `HISTORY_LIMIT` | `10` | Recent individual messages supplied to the follow-up resolver |
| `EVAL_TIMEOUT_SECONDS` | `60` | Evaluation/LLM-judge/live-smoke SDK timeout |
| `EVAL_MAX_RETRIES` | `0` | Evaluation/LLM-judge/live-smoke SDK retry limit |
| `JUDGE_MODEL` | `gpt-4.1-mini` | Model selected by `grade --judge-model` when no model value is supplied |

Model availability still depends on the configured provider/account. `JUDGE_MODEL`
is a configuration default, not a claim that the judge is calibrated. The recorded
[judge audit](../evals/analyses/2026-09-21-judge-calibration.md) still applies.

Blank values use their defaults. Chunk size/token limit, top-k, history limit and
timeouts must be positive; overlap/retries must be nonnegative. In character mode,
overlap must be less than chunk size. These constraints are validated when settings load.
The tokenizer name is resolved when structural chunking runs, before embedding.
Its public vocabulary may be downloaded on first use. Structural chunks have no
overlap; the tokenizer counts source text and does not change the embedding model.
The 512-token default has not yet been validated through a retrieval-quality comparison.

## Precedence and temporary overrides

From highest to lowest priority:

1. Explicit entry-point overrides, such as CLI flags.
2. Process environment variables.
3. The `.env` file in the current working directory.
4. Defaults in `Settings`.

Run commands from the repository root so they find the intended `.env`.

An existing `.env` retains precedence over the new `data/v1` default. For isolated
v1 development, use `DATA_DIR=data/v1 make app` (or `make api`) and
`uv run --locked python main.py --data-dir data/v1`. These commands reuse `.env`
credentials without modifying the old library or the configuration file.

```sh
# Use all configured defaults.
make app
uv run --locked python main.py
uv run --locked python -m evals.evaluate run --label "Configured baseline"

# Override only the selected options for one invocation.
uv run --locked python main.py --model alternative-model --top-k 8
uv run --locked python -m evals.evaluate run --label "Top-k experiment" --top-k 8

# Explicitly request paid model grading using JUDGE_MODEL.
uv run --locked python -m evals.evaluate grade evals/runs/<run-id> --reviewer experiment-judge --judge-model

# Explicitly request a different judge for one invocation.
uv run --locked python -m evals.evaluate grade evals/runs/<run-id> --reviewer experiment-judge --judge-model alternative-model
```

The interactive CLI supports `--model`, `--top-k`, and `--data-dir`. Evaluation runs
also support `--embedding-model`, `--chunking-strategy`, `--chunk-max-tokens`,
`--chunk-tokenizer`, `--chunk-size`, and `--overlap`. The last two apply only to
character mode. Explicit overrides
are validated together with the remaining configured values. A blank resolver model
follows the effective answer model, including a `--model` override.

Evaluation metadata records the resolved generation model, embedding model, chunking,
top-k, timeout, and retries. Historical run artifacts are unchanged. Setting
`JUDGE_MODEL` alone never starts grading. Human grading, report rendering, comparison,
and history listing remain offline and do not load credentials.

## Changes that affect stored data

- Answer/resolver model, top-k and history-limit changes apply after restart and do
  not require reindexing.
- Chunking strategy, token budget/tokenizer, and character size/overlap changes apply
  only to newly indexed files. Existing chunks and
  saved evidence snapshots do not change. Re-upload files to apply new chunking.
- Changing the embedding model requires a fresh index of **all** documents. Use a
  new `DATA_DIR`, restart, then upload the original TXT or Markdown files. A same-dimensional
  model can still use an incompatible vector space. The application does not
  migrate or detect that mismatch automatically; do not query an old index with
  a different embedding model. A new data directory also starts a new library and
  conversation store; the previous directory remains intact.

## Code ownership of configuration

Entry points instantiate `Settings` once and pass the selected models and numeric
options to providers/services. Low-level functions do not read `.env` or require
credentials: direct Python callers pass overrides explicitly, or use the shared
`DEFAULT_*` constants in `config.py`. Keeping default literals in one module avoids
API/CLI/evaluation drift without making every chunking or storage call load settings.

Prompt text, HTTP routes, SSE event names, database schema/filenames, the cosine
index contract, and development-server ports remain implementation or launcher
settings. They are not model-tuning options; changing these contracts is not an
`.env` switch. No hybrid-search/reranker settings are introduced before those
components exist.
