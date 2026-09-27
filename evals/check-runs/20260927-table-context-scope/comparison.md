# Offline table context and scope comparison

The final replay preserves **16/16 requested fact instances** in the actual
serialized context for the four original requests that reached retrieval,
compared with **2/16** at product baseline `b792448`. All six original questions
now resolve to the ready PDF locally, compared with four before the fix.

This is evidence and scope verification, not a new answer-quality result. The
two originally scope-blocked requests have no recorded retrieval candidates;
their eight requested fact instances are excluded from the four-case packing
denominator and remain untested as full requests. No provider or paid judge was
called, and the original failed live acceptance results remain unchanged.

## Dense-table replay

The [protocol](replay-protocol.md) fixes the original corpus, three questions,
fact annotations, source spans, selected rank order, expanded parent inputs and
4096-token evidence budget. [Frozen inputs](frozen-inputs.json) were constructed
before product context/packing edits. Baseline replay reproduces the original
packed chunks, token counts, exclusions and unexpanded parents exactly.

| Original request | Baseline context tokens | Final context tokens | Baseline covered facts | Final covered facts |
| --- | ---: | ---: | ---: | ---: |
| dense-table / single | 305 | 3651 | 1/5 | 5/5 |
| dense-table / planned | 305 | 3651 | 1/5 | 5/5 |
| state-totals / single | 305 | 3651 | 0/3 | 3/3 |
| state-totals / planned | 0 | 3346 | 0/3 | 3/3 |
| grouped-and-blank-cells / single | 0 | 0 | No original candidates | Scope only; no candidates replayed |
| grouped-and-blank-cells / planned | 0 | 0 | No original candidates | Scope only; no candidates replayed |

The table source `child:0` now takes 3346 tokens when serialized alone and fits
alongside the 305-token disclaimer source. The cell coordinates, source slices,
physical page, offsets, full header paths and blank positions are preserved.
Actual serialized table JSON decodes to the exact retained metadata; source
bodies and separately located header supplements match their canonical text.
The [final comparison](analysis-2/comparison.json) records these checks and every
fact's required cell/header provenance. Its
[20-metric inventory](analysis-2/measurement.json) separates local structural
coverage and frozen-rank diagnostics from unexercised answer quality and billing.

Compacting JSON alone was insufficient. The retained
[first comparison](analysis-1/comparison.json) improved coverage only to 12/16:
the top-ranked disclaimer's table-bearing parent became small enough to fit
(3382 tokens), consumed the budget, and blocked `child:0` at a combined 6728
tokens. The final packing change admits selected children before expanding PDF
table parents, then upgrades to a parent only when the other admitted sources
still fit. This preserves the selected disclaimer and target table together.

## Blank-cell fixture

The [separate fixture audit](blank-fixture-1/audit.json) explicitly serializes the
already known `child:0`. It retains all four grouped/blank-cell facts: ungrouped
Handgun 23,022, Pre-Pawn Handgun 14, and the blank Rentals Handgun and Rentals
Long Gun cells. Both blanks retain interior zero-width source spans at their
original columns, with the Rentals parent header, Handgun/Long Gun leaf headers,
row label and report date. No blank is converted to zero.

That fixture verifies source representation only. It supplies no new retrieval
ranking and does not establish that the previously blocked question now receives
a correct or supported model answer.

## Financial controls

Six previously frozen Apple financial question/mode selections retain **16/16
requested fact instances before and after**, with the complete unit sentence and
its share/per-share exceptions additionally checked on all six. Exact table
tuples preserve the quarter/year associations and September 28, 2024 date;
substring presence alone is insufficient. See the
[financial control comparison](financial-control-1/comparison.json) for all
source-bound checks, metadata, selected ranks, admitted identities and metrics.

| Financial control | Baseline context tokens | Final context tokens |
| --- | ---: | ---: |
| apple-sales / single | 2712 | 3188 |
| apple-sales / planned | 2712 | 3643 |
| apple-income / single | 2712 | 3643 |
| apple-income / planned | 2712 | 3643 |
| apparent-conflict / single | 3884 | 3188 |
| apparent-conflict / planned | 4019 | 3323 |

Admitted identities can change when more complete parent context fits. For
example, `apple-sales / single` upgrades from `child:2` to `parent:1` while
preserving the same requested values, period columns and units. Full identifiers
are retained in the artifacts. All contexts remain within 4096 tokens, and
parent text does not coexist with its own child text.

## Failures and limits

- [baseline-1](baseline-1.log) retained a harness assertion failure: the planned
  caller and direct scope resolver use different not-found messages. Their
  status, references, matches and file IDs agree. The successful
  [baseline-2 record](baseline-2.json) compares those fields independently and
  preserves the wording difference.
- [after-1](after-1/manifest.json) preserves the incomplete compact-only result;
  [after-2](after-2/manifest.json) is the final packing result.
- Local packing/scope timings are single-pass diagnostic measurements. They do
  not establish production response latency, throughput or provider cost.
- Original planned queries and ranks were chosen under the old evidence and
  sufficiency cycle. They are deliberately fixed here; a new live planned run
  may change its queries or stopping decision.
- New answer correctness, completeness, faithfulness, citation support,
  abstention and blank-cell generation remain unmeasured. These offline results
  do not establish live acceptance or authorize a merge.
