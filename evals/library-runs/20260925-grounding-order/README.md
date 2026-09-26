# Instruction placement — failed verification

Commit `e382871` moves the same developer instructions after the unchanged user
question/evidence message. Exact source content and roles are preserved. Full
backend checks: 557 passed, 1 intentionally skipped live-provider test. Earlier
assertion/collection failures and corrections remain in the
[check records](../../check-runs/20260925-grounding-order/README.md).

Five saved-context GPT-4.1 calls, once each, no retries. **3/5 cases pass; overall
acceptance fails.** The header status no longer adds universal endpoint scope,
but the wrong-FAQ scholarship attribution persists and limited scholarships are
omitted. The personal-status answer now adds a contact whose source only covers
course eligibility; it does not support this personal approval/supervisor issue.
This prevents a claim that message placement fixes grounding generally.

[PLAN.md](PLAN.md), [REVIEW.md](REVIEW.md), [acceptance.json](acceptance.json),
[before metrics](before-metrics.json) and [after metrics](after-metrics.json)
preserve the frozen criteria, every raw answer/source and all claims. Codex is
the reviewer/implementer, not an independent human. The personal answer withholds
the requested facts but fails the no-unsupported-advice criterion: 1/2 appropriate
abstentions, 0/3 incorrect refusals on answerable cases. No paid judge was run.

Correctness: 95.45% over 11 reference points. Faithfulness: 24/25 claims (96%).
Citation support: 21/24 pairs (87.5%). Local supporting citation coverage: 21/25
claims (84%), but the personal answer has no supported factual citation, so the
per-answer gate fails. Every call completed; no error/timeout/retry or invalid ID.
Generation completion mean/P50/P95: 2.519/2.009/4.176 s; first nonempty generation
delta: 0.929/0.872/1.317 s (N=5, median P50, nearest-rank P95, provider wait included,
service/HTTP excluded). Input/output: 17,286/853 tokens. Actual billing unavailable.
Model resolved to `gpt-4.1-2025-04-14` on both sides. No new retrieval/ingestion;
all inherited evidence/rankings are labeled. One historical sample does not prove
a causal improvement. The next [model comparison](../20260925-grounding-model/PLAN.md)
uses unchanged messages and gates. No local settings change or merge is implied.
