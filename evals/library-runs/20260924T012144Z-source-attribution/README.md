# Source Attribution Prompt: Initial Attempt

Status: rejected in favor of the [revised prompt experiment](../20260924T012523Z-source-attribution-v2/README.md).

This run replayed the 18 frozen cases and exact final evidence from the preceding
packing experiment through production `stream_answer` and `StreamingLLMClient`.
Each case ran once with the old prompt and once with the initial candidate,
alternating order at concurrency 1. Only developer instructions changed. Models,
question text, evidence text/order, and source numbering were fixed. The 36
generation requests succeeded with zero retries; no retrieval or indexing ran.

The candidate recovered the CPT FAQ's after-first-year statement, but explicitly
inferred that it applied to the regular program, not the Industry Concentration.
The source does not establish that distinction. This failed the intended source
attribution behavior. The old-prompt answer omitted the FAQ timing entirely.
The observed case, raw answers and all other outputs are retained, not replaced
by the revised experiment.

| Generation-only timing, seconds | Baseline mean / P50 / P95 | Candidate mean / P50 / P95 |
| --- | ---: | ---: |
| First nonempty delta | 0.700 / 0.567 / 2.026 | 0.716 / 0.539 / 1.597 |
| Stream completion | 2.185 / 1.833 / 5.262 | 2.293 / 1.908 / 4.193 |

Each distribution has 18 samples; nearest-rank P95 is the maximum. These are
provider generation-stage timings, excluding query embedding, retrieval,
reranking, packing and app HTTP. Do not compare them to earlier end-to-end times.
Host/network/provider cache variation is uncontrolled; offline tests overlapped
part of this run. No speedup or production-capacity claim follows.

Evidence coverage is unchanged at 99.96% annotated-character recall and 68.75%
full-span recall across 16 answerable cases. `metrics.json` includes the full
inventory, binary annotation-overlap retrieval proxies and unavailable/not-applicable
statuses. Full answer quality was not graded for this rejected candidate; the
focused CPT development review below is not independent human grading.

- Baseline provider tokens: 57,329 input, 3,689 output.
- Candidate provider tokens: 60,011 input, 4,284 output.
- Billing data unavailable; no paid embedding or rerank calls in this replay.
- Full offline backend suite for this initial prompt: 477 passed, 1 skipped.
  See `backend-tests.log` and `offline-checks.json`; mocked tests do not measure
  live quality or production performance.

`run.json` preserves code/input hashes and settings. `answers.jsonl` preserves
exact messages, sources, deltas, timings, provider usage and errors.
`input-audit.json` verifies identical user messages and evidence between arms.
`ranking-diagnostics.json` contains frozen top-5 child annotation-overlap metrics,
not exhaustive semantic relevance labels. `batch.json` records overall wall time.
The metric collector is [summarize.py](../20260924T012523Z-source-attribution-v2/summarize.py);
output files refuse overwrite. The unused `run_judge.py` is the initial harness
draft; its dict-serialization bug was found and corrected in the revised run.
