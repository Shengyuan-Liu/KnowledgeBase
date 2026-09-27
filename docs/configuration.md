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
| `ANSWER_REASONING_EFFORT` | Blank: omit provider parameter | Optional `none`, `low`, `medium`, `high`, `xhigh` for compatible answer models; API, CLI, evaluation and live smoke test |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Both document and query embeddings in every entry point |
| `RERANK_ENABLED` | `false` | Optional reranking in API, streamed chat, CLI, and evaluations; requires hybrid retrieval |
| `RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | Local cross-encoder model ID or model directory, independent of ANSWER_MODEL |
| `RERANK_DEVICE` | `auto` | Select available CUDA, MPS, or CPU; accepts explicit `cuda`, `mps`, or `cpu` |
| `RERANK_BATCH_SIZE` | `4` | Local inference batch size |
| `RERANK_MAX_PAIR_TOKENS` | `1024` | Per-pair limit using the model tokenizer; oversize fails without truncation |
| `RERANK_CANDIDATE_LIMIT` | `20` | Maximum leading RRF candidates scored before top-k selection |
| `RERANK_MAX_INPUT_TOKENS` | `16384` | Aggregate rerank pair-text budget; oversize fails without truncation |
| `RETRIEVAL_MODE` | `single` | `single` or `planned` for API requests without an explicit mode and CLI; browser checkbox selects its own mode |
| `PLANNER_MODEL` | Blank: use `ANSWER_MODEL` | Strict JSON-schema planner for planned requests |
| `PLANNING__SUFFICIENCY_ENABLED` | `true` | Assess final packed evidence after each planned round; `false` retains the stage 3 controller |
| `PLANNING__MAX_ROUNDS` | `3` | Planned retrieval/assessment round cap; 1–3, with six executed logical queries total |
| `PLANNING__*` | See linked limits | Nested [planning budgets and deadlines](planned-retrieval.md#request-bounds); do not affect single mode |
| `RESOLVER_MODEL` | Blank: use `ANSWER_MODEL` | Follow-up question rewriting in API and CLI |
| `CHUNKING_STRATEGY` | `parent_child` | `structural`, `parent_child`, experimental `semantic`, or the MVP `character` baseline, for new uploads |
| `SEMANTIC_SIMILARITY_THRESHOLD` | `0.5` | Split paragraph sentences below this cosine similarity; range [-1, 1] |
| `SEMANTIC_BATCH_SIZE` | `32` | Maximum sentence inputs per semantic embedding call |
| `CHUNK_MAX_TOKENS` | `512` | Structural chunk or child token limit; experimental starting value |
| `CHUNK_TOKENIZER` | `cl100k_base` | tiktoken encoding for splitting and evidence packing |
| `PARENT_MAX_TOKENS` | `1536` | Parent token limit in `parent_child` and `semantic` modes |
| `EVIDENCE_PACKING_STRATEGY` | `parent_then_child` | Keep admitted parents, then fit whole children of omitted parents; `parent_first` is the control |
| `EVIDENCE_MAX_TOKENS` | `4096` | Exact evidence budget, including source file/heading metadata, labels and separators, for all strategies |
| `CHUNK_SIZE` | `2048` | Maximum characters per chunk in `character` mode only |
| `CHUNK_OVERLAP` | `256` | Character overlap in `character` mode only |
| `RETRIEVAL_STRATEGY` | `hybrid` | BM25 + vector + RRF; `vector` selects the vector-only control |
| `RETRIEVAL_CANDIDATE_LIMIT` | `20` | Maximum candidates per route in hybrid mode |
| `BM25_K1` | `1.2` | Finite, nonnegative lexical term-frequency saturation |
| `BM25_B` | `0.75` | Lexical length normalization in [0, 1] |
| `RRF_K` | `60` | Finite, nonnegative reciprocal-rank constant |
| `RETRIEVAL_TOP_K` | `5` | Selected child/flat hits before parent deduplication and evidence packing |
| `HISTORY_LIMIT` | `10` | Recent individual messages supplied to the follow-up resolver |
| `EVAL_TIMEOUT_SECONDS` | `60` | Evaluation/LLM-judge/live-smoke SDK timeout |
| `EVAL_MAX_RETRIES` | `0` | Evaluation/LLM-judge/live-smoke SDK retry limit |
| `JUDGE_MODEL` | `gpt-5.4-mini` | Model for `make eval` and `grade --judge-model` without an explicit model |
| `JUDGE_REASONING_EFFORT` | `high` | Reasoning level for evaluation/calibration; `off` omits the API option for non-reasoning models |
| `JUDGE_CONCURRENCY` | `4` | Concurrent answer reviews in `make eval`; RAG requests remain sequential |
| `JUDGE_TIMEOUT_SECONDS` | `180` | Per-call timeout for the three-stage judge; separate from RAG request timeout |

Model availability still depends on the configured provider/account. `JUDGE_MODEL`
is a configuration default, not a claim that the judge is calibrated. The recorded
[judge audit](../evals/analyses/2026-09-21-judge-calibration.md) still applies.

Blank values use their defaults. Chunk size/token limit, top-k, history limit and
timeouts must be positive; overlap/retries must be nonnegative. In character mode,
overlap must be less than chunk size. These constraints are validated when settings load.
In parent-child and semantic modes, the child limit must not exceed the parent limit, and the
parent limit must be below the evidence budget. Evidence is packed as whole
regions; see [parent-child retrieval](parent-child-retrieval.md). The budget does
not count system instructions, questions, or generated answers.
The tokenizer name is resolved when token-based chunking or evidence packing runs.
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

Retrieval settings take effect after restart and do not require re-uploading files.
See [hybrid retrieval](hybrid-retrieval.md) for route and selection semantics.

The interactive CLI supports `--model`, `--top-k`, `--data-dir`, `--rerank` /
`--no-rerank`, `--rerank-model`, and `--evidence-packing-strategy`. Evaluation runs
also support `--embedding-model`, `--chunking-strategy`, `--chunk-max-tokens`,
`--chunk-tokenizer`, `--parent-max-tokens`, `--evidence-max-tokens`, `--chunk-size`,
`--overlap`, `--retrieval-strategy`, `--retrieval-candidate-limit`, `--bm25-k1`,
`--bm25-b`, `--rrf-k`, `--rerank` / `--no-rerank`, `--rerank-model`,
`--rerank-candidate-limit`, and `--rerank-max-input-tokens`. Character size and overlap apply only to character mode. Explicit overrides
are validated together with the remaining configured values. A blank resolver model
follows the effective answer model, including a `--model` override. A blank rerank
model uses the BGE default independently of the answer model. Setting a rerank model alone does not enable scoring.
Set `RERANK_ENABLED=true` and restart to use the integrated pipeline without
re-uploading files. `RETRIEVAL_STRATEGY=vector` requires reranking to be disabled.
Each nonempty scoring window runs local cross-encoder inference before answer
generation. Initial startup downloads and loads model weights; subsequent runs
reuse the Hugging Face cache. See [reranking](reranking.md) for score semantics and
the two distinct token budgets.

Evaluation metadata records the resolved generation model, embedding model, chunking,
top-k, rerank options and effective model, timeout, and retries. Historical run artifacts are unchanged. Setting
`JUDGE_MODEL` alone never starts grading; `make eval` explicitly starts both RAG evaluation and model grading. Human grading, report rendering, comparison,
and history listing remain offline and do not load credentials.

## Changes that affect stored data

- Answer/resolver model, top-k, evidence budget, and history-limit changes apply after restart and do
  not require reindexing.
- Chunking strategy, parent/child token limits, and character size/overlap changes
  apply only to newly indexed files. Changing the tokenizer affects new chunks
  and future evidence packing; existing chunk token metadata is retained. Existing chunks and
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
`.env` switch.

### Parent scoring option

`RERANK_UNIT` defaults to `child`. Set it to `parent` with reranking enabled to
score unique whole-parent regions from the fused candidates. This changes the
meaning of the rerank candidate cap to unique regions; raw route windows remain
child-based. See [parent reranking](parent-reranking.md) for scoring provenance,
input limits and the separately measured evidence-budget tradeoff. The API, CLI
and evaluation entry points receive this option through `Settings`.

`ANSWER_REASONING_EFFORT` is optional and must be supported by the selected answer
model. Blank omits the parameter entirely, preserving non-reasoning model calls.
A separate `RESOLVER_MODEL` does not receive this setting; when the resolver shares
the answer client, it also shares that client's reasoning option. Judge reasoning
remains controlled separately by `JUDGE_REASONING_EFFORT`. Model comparison records
do not silently change the local `.env` or the checked-in default model.
