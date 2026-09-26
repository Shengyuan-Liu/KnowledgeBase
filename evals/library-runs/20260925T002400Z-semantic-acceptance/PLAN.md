# Frozen semantic-chunking acceptance comparison

Prepared before observing either new configuration. The [plan](plan.json),
[cases](cases.json), [corpus hashes](corpus.json) and [canonical block units](blocks.json)
are frozen inputs. Eighteen existing development questions and six newly authored
acceptance questions run on the same 17-document snapshot. The latter are a small
Codex-authored holdout on familiar documents, not independent human labels or a
new data population. They are reported separately, with no tuning after outputs.

Both modes use GPT-4.1, text-embedding-3-small, hybrid retrieval, local BGE reranking,
top-k 5, 512-token children, 1536-token parents, and a 4096-token formatted evidence
budget. Only `CHUNKING_STRATEGY` changes from `parent_child` to `semantic`, with
the preselected 0.5 similarity threshold and sentence batches of 32. Judge protocol
v11, its source hash, model, high reasoning and four workers are fixed. SDK retries
are zero. All data is isolated under the experiment's directory below `data/evals`.

Run collection for both modes first, then judge both saved batches once. No
automatic historical regrading, calibration tuning or rerunning failed judgments.
Record failures as failures. Preserve exact question outputs, evidence, route
rankings, source identity, budget exclusions, settings and available provider usage.

Primary retrieval comparison uses fixed annotated character/span coverage.
Secondary ranking projects ordered child hits onto unique canonical parser blocks
(source order inside a hit), uses binary overlap with frozen gold spans, and
reports Recall/Precision/Hit Rate/MRR/NDCG at K=5 per stage. These labels are an
incomplete relevance proxy. Raw child-based metrics are retained for diagnosis
but are not directly compared after rechunking. Check actual stored parent spans
are identical across both modes before interpreting the intervention.

Time the in-process production stream from request start to the first answer delta
and iterator completion (including persistence). HTTP transport is excluded.
Separate ingestion, model loading, embedding, reranking, packing and generation.
Search/fusion has no independent instrumentation and remains unavailable. Report
mean, median P50 and nearest-rank P95. Sequential RAG throughput is not a load test;
host/provider load and warm caches are uncontrolled. Billed dollars remain
unavailable if the provider does not return them; token counts are not dollar cost.

Codex reviews all six new-case answers in each mode and all paired coverage,
correctness and faithfulness regressions against actual supplied evidence. Retain
judge disagreements and missing measurements. This is not independent human
grading. Keep structural chunking as the default unless user acceptance and
evidence justify a later change. Passing results do not authorize a merge.

Reproduce in a new run directory; this directory is append-only:

```bash
PYTHONPATH=. uv run --locked python evals/library-runs/20260925T002400Z-semantic-acceptance/run_pair.py collect
PYTHONPATH=. uv run --locked python evals/library-runs/20260925T002400Z-semantic-acceptance/run_pair.py grade
```
