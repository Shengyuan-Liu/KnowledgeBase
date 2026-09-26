# Explicit named-source instructions — failed verification

Production commit `e2537c3` added named-document attribution and literal table-status
instructions. Seventy related tests passed. Five unchanged saved-context questions
were then generated once each with GPT-4.1 (`gpt-4.1-2025-04-14`), timeout 60 s,
zero retries, concurrency one. **3/5 case results pass, but the overall frozen gates
fail.** The endpoint scope and wrong-FAQ attribution remain; the awards response
also omits the limited number of scholarships. Extra summary claims lack local
citations. This is not a completed semantic fix.

[PLAN.md](PLAN.md) and `freeze.json` precede calls. Exact user/evidence messages and
annotations match the [previous five-case attempt](../20260925-source-scope/README.md).
Only developer instructions changed. No ingestion, retrieval, paid judge, output
repair or same-prompt retry. Raw calls, sources, deltas and outputs are append-only.
[REVIEW.md](REVIEW.md) contains all answers and claim/source quotes with offsets.
Codex reviewed all 28 factual claim occurrences, not an independent human review.

| Metric | Value |
| --- | --- |
| Correctness | 90.91%, 11 reference points |
| Supported claims | 26/28, 92.86% |
| Supported associated citation pairs | 22/25, 88.00% |
| Claims with local supporting citations | 22/28, 78.57% (below the frozen 80% gate) |
| Appropriate / incorrect abstention | 2/2 unavailable cases; 0/3 answerable cases |
| Completed provider requests | 5/5, no errors/timeouts/retries |
| Generation completion | Mean 2.300 s, P50 2.331 s, P95 2.886 s |
| First generation delta | Mean 0.904 s, P50 0.875 s, P95 1.025 s |
| Input / output usage | 17,286 / 749 tokens; billed cost unavailable |

N=5 for timings; median P50, nearest-rank P95, provider waits included, service and
HTTP excluded. No causal claim from a single historical comparison. Complete
inventory, inherited retrieval provenance, configuration, usage, throughput and
per-case results are in [before metrics](before-metrics.json),
[after metrics](after-metrics.json) and [acceptance.json](acceptance.json).

The original `manual-review.json` mistakenly treated one API-error status sentence
as a separate paragraph. It actually shares the paragraph with citation [1].
[review-correction.json](review-correction.json) documents the correction;
[qualified-manual-review.json](qualified-manual-review.json) is used for metrics.
Original review, answers and criteria remain unchanged. This reviewer correction
does not change the failed overall verdict.

This failed attempt motivates a separate controlled change to instruction
placement, recorded in [the next frozen plan](../20260925-grounding-order/PLAN.md).
It does not authorize a merge.
