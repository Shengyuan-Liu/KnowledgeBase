# Explicit blank cells and bounded planner coverage

Empty extracted cells now use an explicit state=blank observation instead of a
bare null. Model context instructs the answer to call the source cell blank,
without inferring zero or an unavailable excerpt. Canonical text, original cell
coordinates and page provenance remain unchanged; old null readings remain defined.

The recorded failed planner response declares comparison requirement r4 but maps
no query to it. Planner v3 requests complete comparison associations. For an
unaddressed decomposed requirement, one additional query uses the unchanged resolved
question and the missing IDs, within the existing six-query limit. The raw model
output is preserved and the added query is separately recorded. Unknown IDs and
exhausted slots still fail validation; there is no second planner/provider call.

[Scoped verification](scoped-1.json): 278 tests passed, with one existing
Starlette/AnyIO deprecation warning. The exact recorded orphan plan is recovered
with four queries, and an HTTP/SSE regression verifies execution, document scope,
trace persistence and history parity. Tests retain the six-query bound and rejection
of unknown IDs. These are offline mocked-provider checks, not live quality scores.

The [matched packing replay](comparison-1/comparison.json) uses the same immutable
twelve source snapshots/selections as before, referenced by path/hash rather than
duplicating the corpus. All 24 dense-table and 16 financial evidence points remain
covered. Dense contexts rise from 2,518 to 2,604 tokens (one 2,213 to 2,299).
Financial contexts rise by 60 tokens to 3,724-4,041, within 4,096, retaining all units
and period associations. Every cell binding is checked against its original cell.
Exact before/after contexts, evidence, source hashes and all 20 metrics are retained.
This replay isolates representation; the separate planner failure had no retrieved
candidates and is exercised by the recorded-response regression tests.

The [live protocol](../../library-runs/20260927-blank-plan-acceptance/protocol.md)
freezes one six-request acceptance pass after the implementation commit. It does
not authorize additional retries, broad evaluation or a merge.
