# Multi-Source Answer Completeness and Attribution

Status: prompt and regression tests implemented on `v1`. User acceptance and
merge approval remain pending. Required CPT facts improved, but source naming
and full semantic evaluation remain unresolved; this is not a clean acceptance.

## Change

The shared JSON/streaming generation instructions now ask the model to inspect
all excerpts for each named source, distinguish similarly named pages, present
different timings/conditions side by side, and leave their relationship
unexplained unless explicit evidence connects them. They prohibit inventing
group eligibility, exceptions or precedence from a specialized page title.
No additional model call, answer repair, retrieval change or new UI was added.

The [initial attempt](../20260924T012144Z-source-attribution/README.md) recovered
a missing fact but still invented a regular-program exception. Its 36 outputs
and metrics are retained separately. The revised instructions tested here are
the delivered version in `knowledgebase/rag/generation.py`.

## Controlled comparison

- Same 18 questions, annotations, and exact final evidence from the
  [packing run](../20260924T004817Z-child-first/README.md): 16 answerable cases,
  two unanswerable cases; original snapshot of 17 files, 38 parents, 92 children.
- 36 fresh generation calls, alternating baseline/candidate order, concurrency 1,
  GPT-4.1, timeout 60 seconds, zero SDK retries, no warmup. Exact returned model
  names and provider usage are stored per response. Provider cache behavior and
  network/host load were uncontrolled; offline checks overlapped part of the run.
- Production `stream_answer` and `StreamingLLMClient` executed with the old or
  revised developer prompt. `input-audit.json` verifies byte-identical user
  messages and sources for every pair. Only developer instructions changed.
- Retrieval, BGE ranking, top-k 5 and 4,096-token packing were **frozen**, not
  rerun. Frozen traces are in `frozen-evidence.jsonl`. No library mutation or
  daily conversation was needed for this comparison.
- Timings measure SDK generation request to first nonempty text delta and stream
  close, excluding all retrieval stages and app HTTP. They must not be presented
  as end-to-end query latency or compared directly with the earlier 4.81-second
  end-to-end mean. The separate live app smoke below covers the actual route.
- These 18 questions were used during development, not held out. Each arm has
  one sample per question; results do not establish stable population gains.

## Observed result and remaining failures

The revised CPT answer includes all three expected facts: FAQ CPT after the first
year, Industry Concentration internship within the first year, and consultation
with OGS about early CPT. It explicitly says the sources do not explain how the
statements fit together. The fresh baseline instead mixes up the FAQ pages and
adds unsupported standard-program/F-1 interpretation.

**The revised answer is still not fully acceptable:** its heading says
`Admissions FAQ ([3], [4])`, grouping the general FAQ [3] with the actual admissions
excerpt [4]. The timing sentence correctly cites [4], but the source label is
misleading. The live app smoke repeats this broader naming problem. Do not count
complete fact coverage as complete citation/source correctness.

The API-setup answer in both arms omits `anthropic.Anthropic()` from the composite
expected-point annotation. The question itself asks only for the invoking method;
the broader frozen annotation was kept unchanged and this mismatch is disclosed.

Codex reviewed all 36 answers against expected points and topical relevance;
`development-reviews.jsonl` preserves scores, actual answer text and reasons.
This is development review, not independent human grading or exhaustive
claim-by-claim adjudication. Correctness below is the normalized expected-point
rubric (0 missing/wrong, 1 partial, 2 complete/correct), not overall factual accuracy.

| Development-review diagnostic | Baseline | Revised prompt |
| --- | ---: | ---: |
| Expected-point score, mean across 18 questions | 98.15% | 99.07% |
| Fully correct/complete point fraction, macro-average | 96.30% | 98.15% |
| CPT expected-point scores | 1 / 2 / 2 | 2 / 2 / 2 |
| API-setup expected-point scores | 2 / 2 / 1 | 2 / 2 / 1 |
| Topic relevance, mean on 0–2 rubric | 2.0 | 2.0 |
| Appropriate abstention on unanswerable cases | 2/2 | 2/2 |
| Answerable cases with a false missing-information claim | 1/16 | 0/16 |

Other expected-point scores are unchanged in this review. Relevance does not
assess brevity or truth. Incorrect missing-information claims include a falsely
refused subpart, not only refusal of an entire question.

## Latency, usage and reliability

| Generation-only timing, seconds | Baseline mean / P50 / P95 | Revised mean / P50 / P95 |
| --- | ---: | ---: |
| First nonempty answer delta | 0.622 / 0.575 / 1.385 | 0.622 / 0.580 / 0.952 |
| Complete generation stream | 2.111 / 1.958 / 3.723 | 2.754 / 2.296 / 8.314 |

There are 18 samples per arm; nearest-rank P95 is the maximum. All 36 generation
requests completed, with zero errors, timeouts or retries. The revised answers
were longer and the measured completion time increased by 0.643 seconds on
average. This is a real recorded tradeoff, with stochastic/network variation;
it is not a causal latency estimate from repeated trials.

| Provider generation tokens, totals over 18 calls | Baseline | Revised |
| --- | ---: | ---: |
| Input | 57,329 | 60,875 |
| Output | 3,864 | 4,742 |

The additional 36 judge calls used 191,341 input and 10,677 output tokens,
recorded separately in `judge.jsonl`. Billing data is unavailable; no dollar cost
is fabricated. No local BGE computation or embedding calls ran in the replay.
Sequential active-time throughput and total mixed-arm wall time are retained in
`metrics-reviewed.json` and `batch.json`; they do not establish concurrent capacity.

## Retrieval and evidence diagnostics

Both arms use identical fixed evidence: 99.96% annotated-character recall and
68.75% full-span recall over 16 answerable cases. Top-5 selected-child diagnostics
are therefore also unchanged:

| Binary annotation-overlap proxy | Both arms |
| --- | ---: |
| Recall@5 | 0.7795 |
| Precision@5 | 0.3500 |
| Hit Rate@5 | 0.9375 |
| MRR@5 | 0.9375 |
| NDCG@5 | 0.8336 |

A child is labeled positive when its source interval overlaps any frozen gold
span; all other children are treated as zero for this diagnostic. Annotations
are not exhaustive relevance judgments, and large table annotations can include
irrelevant text. These are labeled-overlap proxies, not trustworthy semantic
precision/NDCG estimates. Definitions, positive IDs and per-case values are in
`ranking-diagnostics.json` and the metric inventory. MRR is truncated at 5;
NDCG uses binary gains/log2 discount and precision uses denominator 5. Unanswerable
questions are excluded, not assigned zero recall. No retrieval gain is claimed.

## Evaluator failures and unavailable measurements

The existing protocol-3 judge was applied with `gpt-4.1-mini`, concurrency 3 and
zero retries. Preserve these failures when interpreting the experiment:

1. The initial harness tried `.model_dump()` on an already serialized rating
   dictionary. All raw provider responses and usage were saved first. The bug
   was corrected and the **same raw responses** were validated offline into
   `judge-validated.jsonl`, with no provider retry or quote repair.
2. Only 18/36 responses passed quote/schema provenance checks (11 baseline,
   7 revised). The other 18 have exact-quote validation failures and remain
   invalid. `judge.jsonl` and `run_judge_initial.py` preserve the original attempt.
3. All 18 provenance-valid responses supplied an empty factual-claim list, even
   for substantive factual answers. Their default grounding/citation scores are
   consequently not meaningful. The judge also gave full API-setup point credit
   despite the missing constructor. Passing quote validation does not establish
   semantic grading quality.
4. The first metric aggregation hit division by zero on those empty claim lists.
   The corrected collector reports missing coverage instead of a perfect or zero
   score. `processing-issues.json` records both harness issues and resolutions.

`metrics.json` retains initial judge-subset diagnostics, which are **not suitable
for before/after quality claims**. `metrics-reviewed.json` is the later inventory
using the explicitly labeled Codex expected-point/relevance review. Full-run
faithfulness, citation support and citation coverage remain unavailable because
exhaustive claim review is missing; no aggregate improvement is claimed for them.
Ingestion/index-mutation metrics are not applicable, and replay retrieval-stage
latencies are not applicable because those stages did not execute.

## Verification and live app

The backend suite for the initial prompt passed 477 tests, with one skipped.
After the final wording changed, the affected suite initially had one assertion
failure because it checked an old literal phrase; the assertion was updated to
the equivalent final rule. All 49 affected tests then passed. The final full
backend suite passed **477 tests, with one skipped**, in 13.62 seconds. Its
results are retained in `backend-tests-final.log` and `offline-checks-final.json`.
All earlier failures and command results remain available. The new regression
checks identical JSON/streaming prompt construction and retention of later
evidence; mocked tests cannot establish that a model follows the prompt.

The daily API was restarted with the delivered prompt. One real CPT HTTP stream
took **4.415 seconds to first delta** and **6.960 seconds to completion**; local
reranking took 2.908 seconds and packing 0.00376 seconds. This is one smoke sample,
not a latency distribution. It preserves both timing facts and the unexplained
relationship, but still loosely groups the general FAQ with admissions material.
`app-smoke.json` and `app-smoke-metrics.json` record that request separately.

All 17 files remained unchanged, all eight preexisting conversations were
readable, saved evidence matched the streamed result, and the frontend returned
HTTP 200. One new smoke conversation was added to daily history. No files were
deleted, uploaded or reindexed. No frontend code changed, so frontend/browser
suites were not rerun for this prompt-only change.

`run.json` stores settings, code/input hashes and timing scope. Exact prompts,
messages, sources, event deltas, returned model names and usage are retained.
Run scripts from the repository root with `PYTHONPATH=.` and a new output directory;
writers refuse overwrite. Frozen-evidence replay does not require stopping the app.

Next work should address explicit source identity in the generation input and
repair/calibrate claim-level evaluation before making full answer-quality claims.
Those are separate from this bounded prompt change and require a new comparison.
