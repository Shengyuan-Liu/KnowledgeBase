# Optional answer reasoning configuration

- `backend-1`: 557 passed, 4 failed, 1 skipped. CLI constructor snapshots lacked
  the new explicit `reasoning_effort=None` argument; updated those expectations.
- `backend-2`: **561 passed, 1 skipped**. Existing Starlette/AnyIO deprecation
  warning; intentionally skipped opt-in live-provider test.
- `preflight-1`: 1 passed, 1 skipped. Only the explicit reasoning setting changes
  in the frozen comparison; message contents, roles, sources and order match.

Real SDK serialization tests exercise omitted/low settings in complete and
streaming calls. Runtime tests verify `.env` propagation through API/CLI, and that
an explicit resolver model does not receive the answer reasoning parameter.
Evaluation entry points pass the setting and retain it in metadata/call records.
All command outputs, code hashes, duration/counts and complete metric inventory
are recorded. No mocked check establishes semantic quality.

Documentation review: `.env.example` leaves the setting blank; configuration docs
state scope, supported values and resolver behavior. English text/Markdown and
links to the [frozen live plan](../../library-runs/20260925-grounding-reasoning/PLAN.md)
reviewed. The live comparison is separate; no daily configuration or model default
has been changed while the user's model preference is pending.
