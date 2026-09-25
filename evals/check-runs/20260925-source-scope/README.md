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
