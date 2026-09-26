# Source-scope prompt verification

- `scoped-1`: 68 passed. Shared complete/streaming prompt delivery, preserved
  source text (including explicit restrictions), provider/citation/chat/API tests.
  Existing Starlette/AnyIO deprecation warning; no live calls in this command.
- `preflight-1`: 1 passed, 1 skipped. Exact saved user/evidence messages and frozen
  five-case selection verified. Post-run artifact test skips until results exist.

Each JSON record retains command, duration, code hashes, counts and complete
metric inventory. Mocked delivery checks do not prove semantic model compliance.
The [frozen live plan](../../library-runs/20260925-source-scope/PLAN.md) defines the
separate source-grounded review. Full backend/frontend/browser results from
[the preceding change](../20260925-retrieval-coverage/README.md) are reused;
only the shared answer instructions changed in production.

Documentation review: the new paragraph in `docs/answer-grounding.md` matches the
implemented instruction and distinguishes prompting from output repair. Relative
links above resolve; English text and Markdown formatting reviewed. No automated
runtime metrics apply to this documentation review.

- `final-audit-1`: 5 passed. Frozen inputs, exact sources/deltas, review quotes and
  offsets, unchanged historical failure, complete metric statuses, and current
  documentation links/English formatting verified. These are artifact-integrity
  checks; the live semantic result is separately **failed (3/5)**.

Final documentation review: root README, v1 README, merge readiness, answer
grounding and the run report consistently preserve the failed result and distinguish
source-attribution failure from a fabricated policy. The header interpretation is
explicitly labeled conservative/debatable. No merger approval or completed fix is
claimed. `qualified-before-metrics.json` corrects a nested historical provider-usage
artifact path; the original numeric observations and original file are retained.
