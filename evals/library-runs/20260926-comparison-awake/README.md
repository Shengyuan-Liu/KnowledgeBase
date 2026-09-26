# Awake-host comparison acceptance

**11/11 first-pass service requests and 11/11 frozen strict case reviews pass.**
The comparison now explicitly distinguishes both FAQ documents, including the
General FAQ absence point. All seven answerable questions have 100% annotated
source-span coverage. All 26 inventoried factual claim units, including repeated
claims, have associated supporting citations. Codex reviewed every raw answer,
required point, cited excerpt and identity label; this is implementer review,
not independent human ground truth or held-out accuracy.

This supports recommending a merge of the implemented default v1 path, with the
limitations below. It does not authorize merging or promote experimental semantic
chunking/reranking settings. [Current readiness](../../../docs/v1/merge-readiness.md).

## What changed and what stayed fixed

The prior comparison omitted an explicit General FAQ limitation despite correctly
identifying Admissions. The prompt now uses one labeled item per named document;
the final brevity instruction preserves that format. No postprocessing, repair,
extra generation, reference rewrite, model change or retry was introduced.

The prior three slow/error generation starts align within a second of actual
macOS sleep events. See the [retained diagnosis](../../check-runs/20260926-generation-diagnostics/README.md).
This establishes a host-sleep confound; it does not prove that every old delay was
caused solely by sleep. The new process temporarily holds `caffeinate -i -s`
assertions. [Before](power-assertions-before.log) and [after](power-assertions-after.log)
records show these assertions; [power events during the run](power-events-during.log)
contains no transitions. Saved power settings are unchanged, and the assertion
ends with the process. Maximum active-versus-wall service clock difference is
0.000029 seconds. UTC batch span and monotonic duration now agree closely.

The [plan](PLAN.md) was frozen before calls. Same 11 questions, 17 frozen documents,
v2 annotations, verified copied index, embeddings, GPT-4.1 with reasoning omitted,
structural parent-child 512/1536, hybrid top-5, candidate limit 20 and 4096-token
packing. Reranking disabled. Code `cbd6fba`; exact inputs, prompt hashes, configuration,
resolved models and source spans are retained. No fresh ingestion, judge, warmup
or HTTP/browser workload. Concurrent requests: one; SDK retries: zero; timeout:
60 seconds. Exactly one bounded pass, with no additional paid sampling.

## Per-case comparison

| Case | Previous first pass | This first pass |
| --- | --- | --- |
| Credit load / effort | Pass | Pass |
| Independent study / pass-fail | Pass, 39.05 s | Pass, 2.31 s |
| Course under two areas | Pass | Pass |
| General FAQ awards / jobs | Pass | Pass |
| Header endpoint scope | Pass | Pass |
| Message subfield statuses | Pass, 46.24 s | Pass, 1.29 s |
| Unspecified API error | Timeout, 62.18 s to error | Pass, 1.86 s |
| Personal approval / supervisor | Pass | Pass |
| FAQ comparison | Correct attribution, missing absence point | Both points explicit |
| Ambiguous FAQ | Clarifies without provider calls | Same |
| Missing filename | Clarifies without provider calls | Same |

The old run remains [9/11 strict and 10/11 completed](../20260925-document-representation/README.md),
and its [single recovery](../20260925-scope-timeout-recovery/README.md) remains separate.
[comparison.json](comparison.json) preserves every before/after score, coverage,
timing and finding. Changed prompt and awake-host conditions confound timing
attribution: these are descriptive observations, not proof of a model speedup.
Original broader awards-rubric scoring also remains visible; the optional limited
scholarship-count detail is still omitted. No historical rubric or result changed.

## Measurements

| Timing boundary | N | Mean | Median | Nearest-rank P95 |
| --- | --- | --- | --- | --- |
| Complete service response | 11 | 1.757 s | 1.922 s | 4.016 s |
| First service answer delta | 11 | 1.285 s | 1.381 s | 3.596 s |
| Complete provider generation | 9 | 1.622 s | 1.559 s | 2.434 s |
| First provider answer delta | 9 | 1.050 s | 1.065 s | 2.023 s |

Both active and wall elapsed clocks pass the original mean <=10 s, complete P95
<=20 s and first-delta P95 <=10 s service gates. Two deterministic clarifications
are included in the service population; generation-only and generated-service
populations are separate in [METRICS.md](METRICS.md). Timings include provider waits
and applicable persistence, excluding HTTP/browser and model loading. No production
load-capacity claim from this sequential batch.

18 paid calls: nine query embeddings and nine generations, all successful, zero
retries or judges. Actual generation usage: 28,843 input / 896 output tokens;
query embeddings: 289 tokens. Completed model resolves to `gpt-4.1-2025-04-14`.
Billed dollars are unavailable, not zero. No missing generation usage this time;
previous failed-call usage remains unavailable in its original run.

The [complete inventory](METRICS.md) includes Recall@5, Precision@5, Hit Rate@5,
MRR and NDCG@5 using selected-child gold-span overlap with nonexhaustive relevance
labels, and separate final evidence coverage. Search/fusion lacks independent
instrumentation; reranking, ingestion and lifecycle measurement are not exercised.
Raw [answers/events](answers.jsonl), [provider messages/deltas](calls.jsonl),
[claim/source review](REVIEW.md), [metric JSON](metrics.json), and
[gate results](acceptance.json) remain available.

## Known limitations

`run.log` retains one non-fatal `BoundAsyncStream.__aiter__` finalizer warning:
`ValueError: async generator already executing`. All eleven responses completed;
a read-only database audit verifies their exact answers, source snapshots and
retrieval diagnostics were saved. Twenty-five repeated offline real-SDK/mock-HTTP
streams, with forced garbage collection and unraisable warnings treated as errors,
did not reproduce it. Connection-closing and read-timeout checks pass. This does
not prove all live transport resources are leak-free; the warning's root cause is
unresolved. No dependency internals were patched or warnings suppressed.

Some answers repeat a closing conclusion. The comparison phrases absence at page
level; it matches the inspected frozen General FAQ, but is broader wording than the
prompt's excerpt-level instruction. These are retained wording/style limitations,
not silently changed factual gates. No general reliability or zero-warning claim.

The default local single-user feature can proceed to user acceptance/merge review;
experimental configurations and held-out quality are outside this recommendation.
