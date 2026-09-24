# Dedicated BGE cross-encoder: library comparison

The active reranker is now `BAAI/bge-reranker-v2-m3`, running locally with PyTorch
on Apple MPS. The former OpenAI relevance-scoring provider has been replaced.
This report records functional verification and observed tradeoffs; user acceptance
and merge approval remain separate.

## Reproducible setup

The run used the same 18 frozen questions (16 answerable, two unanswerable),
17 Ready files, 38 parents, and 92 children as the
[earlier LLM rerank comparison](../20260924T000238Z-rerank/README.md).
Cases are byte-identical and stored file/parent/child snapshots match exactly.
No uploads, deletions, or re-embedding occurred.

Both current routes use 20 candidates per retrieval route, RRF k=60, selected
child top-k=5, and a 4096-token numbered evidence budget. BGE scores the leading
20 fused children with exact query/passage pairs and optional heading prefixes.
It returns raw logits, sorted descending; original RRF ranks remain separate.
There is no score threshold, backfill, or question-specific tuning.

Model revision: `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. Local inference uses
float32 weights, MPS, batch size 4, and a 1024-token limit per pair using the model
tokenizer. No candidate text was truncated. Cached model loading took 2.98 seconds,
excluded from query timings. Generation remains `gpt-4.1`, embeddings remain
`text-embedding-3-small`; their existing `.env` credentials are reused. Reranking
makes no paid scoring API request. Local compute and model storage still have a cost.

The runner interleaves routes with three workers. Local inference is serialized on
one shared model. Scoring timings include queue waiting, so these numbers are
neither isolated model throughput nor a single-user latency benchmark.

## Failure and correction

The [first attempt](../20260924T001738Z-bge/README.md) aborted with a native Metal
command-buffer assertion when multiple workers entered MPS inference concurrently.
Its partial answer, configuration, and failure details are retained unchanged.

A per-client inference lock now serializes the shared model. The complete rerun
below finished without a crash. An offline concurrent-inference regression test
checks that only one forward executes at a time. No CPU or LLM fallback was added.

## Results

| Measurement | Current hybrid control | Current hybrid + BGE |
| --- | ---: | ---: |
| Completed answers | 18/18 | 18/18 |
| Mean annotated character coverage, 16 answerable cases | 93.707% | 96.832% |
| Full annotated span coverage, 16 answerable cases | 62.50% | 65.625% |
| Mean evidence tokens | 2646.89 | 2749.22 |
| Mean total answer time | 2.61 s | 5.67 s |
| Mean scoring-stage time | 0 s | 3.44 s |

The historical LLM rerank run measured 99.957% character coverage and 7.03 seconds
mean total time. BGE's recorded coverage is lower, primarily because of the CPT
regression below. Historical latency is context, not a simultaneous LLM/BGE speed
comparison. No general accuracy or superiority claim follows from these 18 cases.

[reviews.jsonl](reviews.jsonl) contains assistant development inspection of all
18 BGE answers and the three control answers needed to analyze prerequisites,
CPT, and API setup. It includes reference-point findings, issues, and actual source
IDs. These are not independent human grades, and no answer-accuracy aggregate is
reported. Valid citation IDs alone do not establish citation support.

- **Prerequisites improved:** BGE selects admissions children at ranks 1 and 2,
  expanding their parent before FAQ parents. The answer now includes the required
  subjects and Python/R expectations. Character coverage changes from 0% to 100%.
- **CPT regressed:** the link-only admissions child moves from RRF rank 10 to BGE
  rank 2. The actual CPT child is still selected at rank 4, but its 1525-token
  parent no longer fits after earlier parents. Final evidence uses 2986 tokens;
  the omitted region cannot fit whole. Coverage falls from 100% to 50%. The answer
  loses the admissions FAQ's after-first-year statement and misidentifies the
  general FAQ as the requested admissions source. This remains a known failure.
- **GPA remains covered via parent expansion:** BGE does not place the direct
  progress-requirement child first. A sibling still supplies its parent, and the
  answer includes GPA 3.0 and 66% credit completion. This is not a ranking improvement
  over the previous LLM reranker.
- **API setup remains partially incomplete in generation:** both current answers
  include SDK installation, environment variables, and `client.messages.create`,
  but omit the explicit `client = anthropic.Anthropic()` statement. The constructor
  is present in the supplied evidence.
- **Both unanswerable BGE cases abstain:** no personal class time or exact tuition
  total is invented. Negative logits do not themselves trigger abstention.
- The other answerable cases retain their annotated coverage. Small Markdown span
  gaps remain at newline separators, as documented in the earlier comparison.

All 36 answers passed exact-source and evidence-budget checks. All 360 scored
candidate texts/IDs matched stored children, final selection followed logit order,
and source provenance used the highest selected child. See [audit.json](audit.json).

## Application verification

The ignored local `.env` selects BGE and enables reranking. API, streaming chat,
CLI, and evaluation use the same provider; `RERANK_MODEL` no longer follows
`ANSWER_MODEL`. The rebuilt app is running at `http://127.0.0.1:8000`.

[app-smoke.json](app-smoke.json) records a real streamed prerequisite answer,
a JSON follow-up, and exact history restoration. All six earlier conversations
remain readable; the 17-file library is unchanged. The new scoring traces report
BGE, its revision, MPS, and raw logits. Older LLM scores retain the ordinal format.

Verification passed: 472 backend tests (one opt-in live test skipped), 33 frontend
tests, production build/type checking, and nine browser tests. Tests cover local
model loading without downloads, batching, fractional negative scores, exact-token
boundaries, concurrency, API/CLI/evaluation settings, parent packing, failure and
cancellation, historical scores, and desktop/mobile source restoration.

## Artifacts and rerunning

- [run.json](run.json) and [local-model.json](local-model.json): resolved configuration,
  code-diff fingerprint, model revision, device, and startup duration.
- [cases.json](cases.json) and [chunks.json](chunks.json): frozen workload and stored evidence.
- [answers.jsonl](answers.jsonl): every answer, actual evidence, full input/ranking
  trace, coverage, timing, and exclusions.
- [summary.json](summary.json), [audit.json](audit.json), and [reviews.jsonl](reviews.jsonl):
  automatic aggregates, fidelity checks, and assistant inspection.
- [run_evaluation.py](run_evaluation.py) and [run_smoke.py](run_smoke.py): executable runners.

Copy the runners and cases to a new directory for a rerun; they refuse to overwrite
artifacts. Stop the app before the paired runner opens the same data directory,
then run `PYTHONPATH=. .venv/bin/python <new-run-dir>/run_evaluation.py` from the root.
Restart before the smoke script, which adds one conversation. Model generation
still makes paid calls; repeated answers and latency can vary.
