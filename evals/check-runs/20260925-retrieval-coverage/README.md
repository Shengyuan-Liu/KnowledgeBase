# Retrieval Coverage Verification

All commands, versions, working-tree fingerprints, durations and outputs are in
adjacent JSON/log records. Mocked tests do not measure provider cost or live RAG
quality. Real local reranking measurements are recorded separately in the
[parent reranking experiment](../../library-runs/20260925-parent-reranking/PLAN.md).

- Supplement preflight: initial direct `pytest` entry point failed collection;
  corrected `python -m pytest` passed 2 checks. Both attempts retained.
- Retrieval/configuration/persistence scope: 63 passed.
- Full backend first attempt: 548 passed, 6 failed, 1 skipped. The six failures
  expected an exact old options dictionary without `rerank_unit`; update that
  expected contract. Final full suite: **554 passed, 1 skipped**. The skipped
  live-provider test is intentional. Existing Starlette/AnyIO deprecation remains.
- Frontend: **40 passed**; TypeScript and production build passed.
- Browser attempts 1 and 2: 9 passed, 1 failed each. Trace inspection found
  **three** chat POSTs although the test sent only two questions: Stop changed
  the reused DOM button into a submit button during its own click event, causing
  another submission. The initial timer hypothesis was disproved by an open
  cancellation fixture. Give Stop and Send distinct React keys so their DOM
  identities cannot change during activation. Keep the fixture open after a
  partial delta and assert exactly two submissions plus unchanged saved history.
  Final browser run: **10 passed**. Both failure traces/context are retained.
- Supplement provenance audit: 3 checks passed. This is data integrity, not a
  successful full-set judge result: 23/24 valid reviews remain.

The earlier two-case diagnostic initially failed while treating serialized
parent heading JSON as a list. The corrected run passed and retains its output
as `parent-diagnostic-2`; this was an experiment-loader issue, not production
storage. The diagnostic has its own qualified metric inventory and failure record.
