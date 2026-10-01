# Release-blocking continuation and binding fixes

The first closeout replay completed all six original requests, but its financial
answer cited an unheaded continuation on physical page 8. Correct numbers alone
do not establish supported period/unit claims. A synthetic unknown-target case
also exposed a missing target decision despite an explicit bridge sentence.
The original outputs remain in `evals/library-runs/20261001-v2-closeout-matched/`.

The evidence adapter now recognizes the observed adjacent-page continuation:
same section, equal column count, and a first body row incorrectly classified as
currency-valued headers. It retains exact preceding table headers and units as
separate, located source supplements and uses them for the derived table reading.
Canonical extraction and source bytes stay unchanged; no reingestion is needed.
This is a narrow continuation rule, not general multi-page table reconstruction.

Dependency binding now receives the prerequisite search text and instructions to
resolve the placeholder identity independently of the still-unknown attribute.
Literal quote validation, scope limits and bounded execution remain in force.
No fixture target is inserted into product prompts or code.

- `before-regressions.json/.log`: 2 expected failing regression tests retained.
- `scoped.json/.log`: 105 passed, no failures/skips, 4.19 seconds.
- Existing Starlette BlockingPortal deprecation warning remains visible.
- All 20 metrics in each command record are explicitly not applicable to these
  offline tests. No paid calls or runtime quality claims come from this check.
- Relevant PDF packing, assessment, heading context, dependencies and sufficiency
  tests pass. Live before/after acceptance is recorded separately.

Content, paths and formatting reviewed; no merge authorization is implied.
