# Grounding message-order checks

The production change places the same developer instructions after the unchanged
user question/evidence message. Source content keeps the user role. Full backend
coverage is used because the shared generation message contract changed.

Retained attempts:

- `scoped-1`: 66 passed, 4 failed. Existing chat assertions still expected the old
  message positions; corrected to inspect the evidence at its new position.
- `backend-1`: 2 collection errors. An unscoped pytest invocation discovered
  historical experiment tests with duplicate module names. The repository's
  Makefile defines the product suite as `tests/`; subsequent runs use that scope.
- `backend-2`: 548 passed, 9 failed, 1 skipped. Remaining hybrid, parent-child and
  reranking integration assertions also expected evidence in the last message.
  Updated those positions without weakening exact source/follow-up/history checks.
- `preflight-1`: 1 passed, 1 skipped. Frozen replay changes message order only;
  both message contents and roles match the previous attempt byte for byte.

Each JSON retains the command, duration, code hashes, counts, output and full
metric inventory. Mocked tests verify fidelity and contracts, not semantic quality.
No frontend code changed; previous UI/build results are reused.

Documentation review: English Markdown and relative links reviewed; the
[frozen plan](../../library-runs/20260925-grounding-order/PLAN.md) distinguishes
instruction placement from new rules, and live generation from full service
acceptance. Runtime measurements do not apply to documentation review.

- `backend-3`: **557 passed, 1 skipped** (intentionally opt-in live-provider test).
  Existing Starlette/AnyIO deprecation warning. All relevant product checks pass.
