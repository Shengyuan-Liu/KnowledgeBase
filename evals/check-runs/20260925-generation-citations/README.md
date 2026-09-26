# Generation citation checks

The shared prompt now requests claim-local citations, preserves explicit source
behavior and limits advice about missing personal information to supplied guidance.

- `scoped-1.json` / `scoped-1.log`: 67 passed across generation, citation IDs,
  complete/streaming providers, conversation services and chat HTTP endpoints.
  The existing Starlette/AnyIO deprecation warning remains in the log.
- `replay-preflight-1.json` / `replay-preflight-1.log`: 3 passed; fixed-context replay checks
  ensure only developer instructions change, prior reviews match exact answer
  records and protocol, and historical service timings are not reported as fresh.

Each record retains command, code digests, duration, counts and the complete
scope-qualified metric inventory. Mocked tests verify instruction delivery and
evidence preservation; they do not demonstrate model compliance or live quality.
The paid acceptance workload is separately frozen under
`evals/library-runs/20260925-generation-citations/` and runs only after these checks.
