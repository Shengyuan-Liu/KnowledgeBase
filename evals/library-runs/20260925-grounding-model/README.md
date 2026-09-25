# Alternative model, provider-default reasoning — failed

Same five questions/messages as [the placement run](../20260925-grounding-order/README.md),
changing only answer model to `gpt-5.4-mini` (resolved `gpt-5.4-mini-2026-03-17`).
The reasoning parameter was omitted; official documentation identifies its default
as `none`. Once per case, 60-second timeout, no retries, concurrency one. Local
`.env` and product model defaults remain unchanged. No paid judge calls.

**3/5 cases pass; the frozen overall criteria fail.** All associated citations now
have supporting text under the same per-clause association protocol, and personal
contact advice disappears. However, the header answer starts with "Yes" to whether
behavior is the same, then correctly describes different behavior. Preserve this
contradiction. The scholarship answer omits the limited-number qualification and
labels two distinct sources generically as the FAQ. Do not interpret better citation
scores as complete answer correctness.

[PLAN.md](PLAN.md), [REVIEW.md](REVIEW.md), [manual-review.json](manual-review.json),
[acceptance.json](acceptance.json), [before metrics](before-metrics.json) and
[after metrics](after-metrics.json) retain all observations. Codex is the reviewer,
not an independent human; this is a known regression set, not held-out accuracy.

Correctness: 90.91% over 11 points. Faithfulness: 20/21 claims (95.24%). Citation
support: 27/27 pairs. Local supporting coverage: 20/21 claims. Both missing-data
cases abstain appropriately; no incorrect refusal among three answerable cases.
All five calls succeed without retries/timeouts/errors/invalid IDs. Generation
completion mean/P50/P95: 1.364/1.531/1.728 s; first delta: 0.840/0.671/1.226 s.
N=5, median P50, nearest-rank P95, provider wait included, service/HTTP excluded.
Input/output: 17,281/475 tokens; actual billed cost unavailable. No ingestion or
retrieval; inherited rankings/evidence labeled. Different tokenizers/provider
settings and single samples limit comparisons.

The completed [low-reasoning configuration](../20260925-grounding-reasoning/PLAN.md)
will be compared separately with exactly the same messages and frozen criteria.
This run is retained as failed and does not authorize a model change or merge.
