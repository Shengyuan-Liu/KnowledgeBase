# Named-source and table-status verification

- `scoped-1`: 70 passed. Generation, provider, citation, chat and API checks.
  Added similar-FAQ fixtures in both retrieval orders to verify distinct source
  identities and unchanged evidence in both complete and streaming messages.
  Existing Starlette/AnyIO deprecation warning, no live-provider calls.
- `preflight-1`: 1 passed, 1 skipped. Frozen five-case selection, prompt hash and
  unchanged historical user messages verified. Post-run check skips before outputs.

Each record contains command, code hashes, duration, counts, output and complete
measurement inventory. Mocked tests prove delivery/fidelity, not model compliance.
The [frozen verification plan](../../library-runs/20260925-source-attribution/PLAN.md)
defines the separate live review. Prior full backend/frontend/browser checks are
reused because production changes affect only shared generation instructions.

Documentation review: English Markdown, relative links and frozen criteria reviewed.
The plan preserves earlier failures, names the Codex reviewer and distinguishes
fixed-context generation from service/browser acceptance. No runtime metrics apply
to documentation review.
