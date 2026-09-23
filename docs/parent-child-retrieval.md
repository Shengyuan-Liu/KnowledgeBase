# Parent-Child Retrieval

Status: implemented on `v1`; `parent_child` is the default ingestion strategy at
the user's request. `structural` remains available as an explicit flat control.
User acceptance and merge approval are separate. Default selection alone does not
establish an answer-quality gain. The [active-library comparison](../evals/library-runs/20260923T205040Z-parent-child/README.md)
records the first real-provider results and remaining retrieval/budget failures.

## Enable and Index

Use the existing `.env` credentials with an isolated library:

```sh
CHUNKING_STRATEGY=parent_child DATA_DIR=data/v1-parent-child make app
```

Existing `.env` files override built-in defaults. Set `CHUNKING_STRATEGY=parent_child`
there and restart if they still select another strategy. The API,
CLI, and evaluation runner all pass these settings through the same services:

| Setting | Default | Meaning |
| --- | --- | --- |
| `CHUNK_MAX_TOKENS` | `512` | Maximum tokens per searchable child |
| `PARENT_MAX_TOKENS` | `1536` | Maximum tokens per parent context region |
| `CHUNK_TOKENIZER` | `cl100k_base` | Tokenizer for splitting and evidence packing |
| `RETRIEVAL_TOP_K` | `5` | Maximum selected child candidates before parent deduplication |
| `EVIDENCE_MAX_TOKENS` | `4096` | Budget for the exact numbered evidence string |

These are experimental starting values. The child limit must not exceed the
parent limit. In parent-child mode, settings require the parent limit to be below
the evidence budget, leaving room for labels; the actual formatted context is
still checked at retrieval time. All limits must be positive. Character overlap
does not apply to either level.

TXT and Markdown use their existing parser, then the
[parent-child splitter](parent-child-chunking.md). Only child text is embedded and
inserted into Chroma. SQLite saves the canonical source, ordered blocks, parents,
children, and their relationships together with the Ready transition. On indexing
failure that transaction rolls back, partial vectors are removed, and the file
remains Failed. Deletion and interrupted-upload recovery use the existing cleanup
path, including parent records.

Changing the strategy affects new uploads only. Existing flat chunks remain
searchable in a mixed library. Retrieval expands a chunk if its stored parent
relationship exists, regardless of the currently selected ingestion strategy.
Re-upload into a fresh library for a controlled comparison; changing `.env` does
not convert existing chunks.

## Search and Pack

1. Restrict both retrieval routes to Ready files. The default [hybrid service](hybrid-retrieval.md)
   fuses BM25 and vector ranks, then selects `RETRIEVAL_TOP_K` children. The explicit
   vector control selects by increasing cosine distance. Record each selected
   candidate's identity, text, offsets, and route provenance.
2. Keep that selected order and load each child's parent from SQLite. Flat
   candidates keep their original chunk text.
3. Deduplicate parent IDs. A parent's position and distance come from its best
   matched child in the selected retrieval order. Retain all matched child IDs in candidate order. Parent text has
   no separately computed embedding score. Deduplication can leave fewer than
   top-k sources; this stage does not fetch more candidates to fill the list.
4. Greedily pack whole regions in that order. Count the exact `build_context()`
   output, including `[1]` labels and separators, with `CHUNK_TOKENIZER`. Skip any
   region that would exceed `EVIDENCE_MAX_TOKENS`, record its ID, file ID, text
   token count, and `context_budget` reason, then consider the next region.
5. Assign contiguous source numbers to the packed regions and supply those exact
   original text slices to generation. If none fit, return the existing
   insufficient-evidence response without an answer-generation call.

Packing applies to flat strategies as well. It never truncates a parent or joins
unrelated sections. The evidence budget excludes the system instructions,
question, and generated answer: it is not a guarantee about a model's total
context window. Historical snapshots are never repacked after settings change.

## Responses and Saved Evidence

`rag.retrieval.retrieve()` retains its list return value. `retrieve_evidence()`
returns both the packed list and `RetrievalDiagnostics`. Services use the latter.

Every answer source describes the actual text supplied to generation:

- `chunk_id` identifies that evidence region; for an expanded source it equals
  `parent_id`. Flat sources have `parent_id: null` and `matched_child_ids: []`.
- `matched_child_ids` identifies the selected child hits that produced the parent.
- `start_offset`, `end_offset`, `heading_path`, `source_block_indices`,
  `token_count`, `tokenizer`, and `max_tokens` describe the parent or flat chunk.
  Offsets are half-open Python Unicode character indices into the canonical file.
- `distance` is the highest-ranked selected child's cosine distance, or null for
  a lexical-only hit. `fusion` preserves that child's ID, RRF score/rank, and both
  route scores/ranks. These values describe the child, not an embedding of its parent.

JSON answers and SSE `complete` events include `retrieval` with `candidates`,
`excluded`, `evidence_tokens`, `max_tokens`, and `tokenizer`. The SSE `sources`
event already contains the expanded source list. `evidence_tokens` counts the
formatted context; source `token_count` counts only that source text using its
stored tokenizer. These can differ after tokenizer settings change.

Source snapshots include the full parent text and metadata. The supplementary
`retrieval_snapshots` table stores the diagnostics, keyed to
`answer_snapshots.message_id`, in the same exchange transaction. Candidate text
and actual supplied parent text survive source deletion and application restart.
Old snapshots remain readable with `retrieval: null`; `init_db()` adds the new
table without rewriting existing columns. Excluded parent text is not separately
snapshotted: exclusions retain identity, reason, and size, while candidate text
remains available.

The evidence panel labels an expanded excerpt as **Parent passage**, displays its
heading path, and shows the exact supplied text. Citation numbering and deleted
historical-source behavior are unchanged. Candidate and exclusion diagnostics are
available through the API and evaluation records; they do not have a dedicated
frontend view in this step.

## Evaluation and Verification

```sh
uv run --locked python -m evals.evaluate run --label "Parent-child experiment" \
  --chunking-strategy parent_child --chunk-max-tokens 512 \
  --parent-max-tokens 1536 --evidence-max-tokens 4096
```

This command makes real provider calls and creates a fresh evaluation index. It
records the resolved budgets and strategy. `answers.jsonl` stores final parent
sources and `retrieval_diagnostics`; the historical `retrieval` key continues to
hold automatic recall metrics. Recall measures supplied evidence regions, so
larger parent coverage must not be mistaken for better child ranking. Candidate
records allow those stages to be inspected separately. Existing runs are untouched.

Offline verification:

```sh
make test
make test-frontend
make test-browser
```

Backend tests cover actual child-only Chroma indexing, one-hit expansion, parent
deduplication, ordering, mixed old/new files, exact budget boundaries, skipped
regions, failure cleanup, JSON/SSE, history after restart/deletion, CLI reuse,
and isolated evaluation runs. The browser fixture uses parent-child ingestion
with 16-token children to exercise multi-child parent evidence, while mocked
providers keep verification offline. These tests validate wiring and invariants,
not live model quality. BM25 and fusion are now integrated; reranking remains later work.
