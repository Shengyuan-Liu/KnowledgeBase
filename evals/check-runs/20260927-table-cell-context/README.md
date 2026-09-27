# Explicit table cell readings: offline regression

Model context now binds each complete cell to its full column-header path and row
label. An empty extracted cell is serialized as null, explicitly distinct from
zero and an unavailable excerpt. Canonical excerpts, stored cell coordinates,
source offsets, physical pages and separately located headers remain intact.
Historical evidence without a reading aid retains its coordinate representation.
The context format is source-metadata-pdf-v3; no reindex is required.

The [matched comparison](comparison-4/comparison.json) replays six dense-table
selections and six financial controls before/after on unchanged source snapshots,
rankings, facts and budgets. Dense evidence remains 24/24 and financial evidence
16/16, including financial units and period associations. All twelve current
contexts fit 4,096 tokens. Dense contexts fall from 3,651 to 2,518 tokens (one
3,346 to 2,213); financial contexts rise to 3,664-3,981. This is structural
coverage, not generated-answer correctness. Every rendered cell binding is audited
against original extraction cells. Exact before/after contexts and packing output
are retained next to the comparison.

[Scoped checks](scoped-1.json): 275 tests passed, one existing Starlette/AnyIO
warning. The first focused run retained one whitespace-comparison regression;
empty reading output was corrected. The first three replay attempts retain an
import-path error and two harness compatibility errors; none called a provider.
All attempts retain command, source hashes, duration, counts and the full metric
inventory. Live quality, cost and production performance are not claimed here.

The [six-request acceptance protocol](../../library-runs/20260927-table-cell-context-acceptance/protocol.md)
is frozen before launch. Only that complete scoped workload will call providers;
it will compare with the previous 19/24 result and disclose the single-reviewer
limitation. No merge is authorized.
