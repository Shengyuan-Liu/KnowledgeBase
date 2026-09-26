# Grounding correction session — verification still fails

Engineering changes are complete and committed, but **no tested configuration
passes every frozen functional gate**. The current default remains GPT-4.1; local
`.env` is unchanged. Do not claim that the default passes based on another model's
results, and do not recommend unconditional v1 merge.

## Completed changes and verification

- Explicitly match claims/citations to the named document; quote table statuses
  without importing endpoint scope from another row or the question.
- Place the developer instructions after unchanged question/evidence data in both
  complete and streaming generation. Sources retain the user role.
- Add optional `ANSWER_REASONING_EFFORT` through Settings, API, CLI and evaluation
  clients, with requested effort recorded. Blank omits the provider parameter;
  explicit resolver models keep their previous requests. No repair or second pass.
- Full product backend: **561 passed, 1 intentionally skipped live-provider test**.
  Real SDK serialization tests cover omitted/low effort; runtime checks cover
  settings propagation. Prior frontend/browser/build checks are reused.

All five comparisons use the same five known questions, sources, annotations and
frozen original rubric. Each configuration has one sample per question. They are
controlled development observations, not held-out accuracy or causal estimates.
Every failed attempt remains intact; no same-configuration retries or output edits.

| Configuration | Cases passing | Remaining failures |
| --- | --- | --- |
| [GPT-4.1, explicit instructions first](../20260925-source-attribution/README.md) | 3/5 | Endpoint overstatement, wrong FAQ, omitted qualification, citation omissions |
| [GPT-4.1, same instructions last](../20260925-grounding-order/README.md) | 3/5 | Wrong FAQ, omissions, inapplicable personal-contact advice |
| [GPT-5.4-mini, reasoning omitted](../20260925-grounding-model/README.md) | 3/5 | Contradictory Yes to different header behavior; omitted qualification |
| [GPT-5.4-mini, low reasoning](../20260925-grounding-reasoning/README.md) | 4/5 | Wrong FAQ and omitted limited-award qualification |
| GPT-5.4-mini, high reasoning | 4/5 | Scholarship/job details omitted; additional non-English word in personal answer |

The final high-effort answer no longer misattributes the application-process fact,
and every inventoried factual claim/citation is supported. However, it omits the
limited number of scholarships, competitiveness of jobs and semester-by-semester
postings required by the frozen references. Both missing-data cases withhold
personal facts/error payloads correctly. The personal answer also contains one
non-English word; this is separately disclosed as an output-language defect, not
silently corrected or used to change the original factual scoring gates.

This session stops at the preregistered final comparison. No further model/config
sampling is used to seek a passing response. The user's optional model preference
is pending, but none of these candidates qualifies for promotion, so no model or
local configuration is switched regardless of that pending choice.

## Final-run quality and performance

[PLAN.md](PLAN.md), [freeze.json](freeze.json), [REVIEW.md](REVIEW.md),
[manual-review.json](manual-review.json) and [acceptance.json](acceptance.json)
retain the exact criteria, answers, source quotes/offsets and per-case judgments.
Codex is the implementer/reviewer, not an independent human. Correctness uses
11 frozen reference points, with partial scores for the two incomplete scholarship
points. The 19 inventoried factual claim occurrences include repetitions; local
citation association is the original paragraph/list-item rule, not v11 scoring.

| Metric | Low effort baseline | High effort |
| --- | --- | --- |
| Reference correctness | 95.45%, 11 points | 90.91%, 11 points |
| Supported claims | 21/21 | 19/19 |
| Supported associated citation pairs | 20/21 | 19/19 |
| Claims with local supporting citations | 20/21 | 19/19 |
| Appropriate / incorrect abstention | 2/2; 0/3 | 2/2; 0/3 |
| Generation completion mean / P50 / P95 | 1.522 / 1.568 / 1.780 s | 3.898 / 3.743 / 5.035 s |
| First nonempty delta mean / P50 / P95 | 0.848 / 0.812 / 1.002 s | 3.266 / 3.150 / 4.349 s |
| Input / output tokens | 17,281 / 739 | 17,281 / 2,440 |
| Reasoning tokens included in output | 236 | 1,958 |

N=5 for timings; median P50, nearest-rank P95, provider waiting/reasoning included,
no service/HTTP transport or persistence timing. Same resolved model snapshot
`gpt-5.4-mini-2026-03-17`. Five successful requests, no errors/timeouts/retries or
invalid citation IDs; largest input 4,701 tokens. All operational gates pass.
Actual billed cost is unavailable, not zero; do not infer price from token counts.
The entire correction session made 25 generation requests and zero paid judge
requests; prior attempts are part of its cost, not hidden by the last run.

[Before metrics](before-metrics.json) and [after metrics](after-metrics.json) contain
the complete inventory, inherited ranking/evidence provenance, throughput, tokens
and missing/not-applicable reasons. No fresh ingestion/retrieval occurred. High
effort improves citation support in this sample but loses reference detail and
adds output latency/tokens; this is not an overall demonstrated quality win.

[Final check records](../../check-runs/20260925-grounding-high/README.md) verify
raw-message/source fidelity, review quotes, metric inventories and document links
across all five attempts. The preceding full [service acceptance](../20260925-v1-codex-acceptance/README.md)
remains 7/8, unchanged. Remaining work is source-specific completeness and reliable
English output, not additional retrieval features or relaxed acceptance thresholds.
