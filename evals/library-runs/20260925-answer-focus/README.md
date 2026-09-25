# Question-aligned answers — one issue remains

The unchanged default GPT-4.1 passes **4/5** targeted cases under the revised,
question-aligned protocol; the same historical baseline passes **3/5** under that
protocol. **Do not recommend full v1 merge yet.** The awards answer still blends
an admissions-only statement into a response requested from the general FAQ,
without explicitly identifying the other document. It is a supported fact in the
supplied context, not fabricated information; the remaining defect is source scope.

## What changed and what was checked

The shared generation prompt requests concise answers per requested part, avoids
unrequested background/repeated summaries, checks numbered excerpts, and applies
English explicitly to uncertainty/status labels. No default model, local .env,
retrieval, evidence text, output repair or second generation pass changed.

The annotation audit found that the awards question does not ask for job posting
cadence or competitiveness, or the number of available scholarships. Version 2
requires all applicants considered competitively, admit-letter notification, and
no individual job guarantee. Original annotations/scores remain intact. Supported
optional facts still need accurate source attribution. [PLAN.md](PLAN.md) records
this correction and its post-historical-inspection limitation before new calls.
Both versions are retained in [cases.json](cases.json) and
[original-cases.json](original-cases.json). This is not a blind rubric correction.

[Backend checks](../../check-runs/20260925-answer-focus/README.md): 561 passed, one
intentional live-provider skip. Tests verify prompt delivery/evidence fidelity,
not compliance. One bounded provider pass: five requests, once each, zero retries,
zero paid judge calls. Reviewer: Codex, the implementer; not independent human review.

## Actual outcomes

- Headers: correct endpoint distinction and literal version status, all cited.
- Pass/fail: all requested restrictions preserved; a prohibition is still repeated.
  This is a style miss, not an unsupported factual claim.
- Awards: all requested facts correct, but the extra no-separate-application fact
  is not identified as coming from the admissions FAQ. Named-source gate fails.
  Under the original rubric limited scholarship count is also missing.
- API error: no exact HTTP status or JSON body invented.
- Personal study: neither approval nor supervisor invented; no unsupported contact
  advice. Unlike the earlier high-reasoning sample, explanatory text is all English.

All five answers were inspected. No new output-language defect was observed; this
does not establish language reliability. The prior high-reasoning sample would
score 5/5 on v2 factual points, but still fails English; its old 4/5 result is not
rewritten or presented as a passing configuration.

## Quality and performance

| Metric | Historical GPT-4.1 | Current GPT-4.1 |
| --- | --- | --- |
| v2 required-point correctness | 11/11 | 11/11 |
| Original rubric correctness | 95.45% | 95.45% |
| Supported claim occurrences | 24/25 | 19/19 |
| Supported associated citation pairs | 21/24 | 25/25 |
| Claims with local supporting citations | 21/25 | 19/19 |
| Appropriate / incorrect abstention | 1/2; 0/3 | 2/2; 0/3 |
| Named-source compliant cases | 4/5 | 4/5 |
| English compliant cases | 5/5 | 5/5 |
| Generation completion mean / P50 / P95 | 2.519 / 2.009 / 4.176 s | 2.406 / 2.311 / 3.309 s |
| First nonempty delta mean / P50 / P95 | 0.929 / 0.872 / 1.317 s | 1.450 / 0.973 / 2.777 s |
| Input / output tokens | 17,286 / 853 | 17,901 / 539 |

The source-scope gate is separate from claim truth, citation-ID validity and the
clause-level citation association used in prior review. In the awards paragraph,
[1] supports the extra application-process clause, while [1][2] support shared
facts. Do not claim every adjacent citation necessarily supports every clause or
silently inflate wrong-citation counts. The prose still fails to distinguish the
named document from the extra document as the frozen instruction requires.

N=5, sequential, provider wait included, median P50 and nearest-rank P95. Five
successes, zero errors/timeouts/retries; resolved `gpt-4.1-2025-04-14`. Actual billed
cost unavailable, not zero. Provider generation latency excludes retrieval,
persistence and HTTP; no load-capacity or causal performance claim. Longer input
and earlier/later provider variation limit comparison. All operational gates pass.

[Raw answers](answers.jsonl), [calls](calls.jsonl), [exact source review](REVIEW.md),
[acceptance gates](acceptance.json), [before metrics](before-metrics.json) and
[after metrics](after-metrics.json) preserve outputs, both scoring versions, errors,
usage and the complete metric inventory. Retrieval/evidence measurements are
inherited, not rerun. These are known development cases; the earlier eight-case
service result remains 7/8. No further prompt/configuration sampling in this session.
