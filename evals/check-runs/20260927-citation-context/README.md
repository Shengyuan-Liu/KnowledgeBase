# Citation guidance and explicit table context

This offline follow-up addresses two observations from the
[six-request financial replay](../../library-runs/20260927-financial-acceptance/README.md):
the planned income answer omitted a citation on its first bullet, and the sales
assessor selected a value row and units without the period/date headers. No new
answers or paid provider calls were made. The historical citation coverage of
13/14 factual groups remains unchanged; this run does not establish that the model
will now cite every item.

## Changes and boundaries

- Final answer instructions include a concrete two-item example repeating the
  same source citation. This also covers one requirement containing multiple
  facts or periods. Complete and streaming generation receive the same prompt.
- Planned answers receive source-number navigation hints per requirement, derived
  from file identity and spans in the current body/supplement context. Hints are
  explicitly fallible; no quote or citation is inserted into generated output.
- PDF evidence retains parser-derived column-header spans. For a selected table
  passage, normalized requirements separately attach already-supplied headers,
  captions, notes and adjacent text under `table_context`. Attachments preserve
  exact canonical text, offsets, physical pages, table/role and related selected
  IDs. They exclude row-header supplements that may describe a different row.
- Model-selected references, raw responses, statuses and gaps remain unchanged.
  Attached context cannot satisfy the two-selected-passage conflict requirement
  or authorize a supplementary query target absent from its selected passage.
- The evidence panel distinguishes **Selected passages** from application-added
  **Table context**. New snapshots preserve both across reload and file deletion;
  older snapshots remain readable without retroactive enrichment.

These changes preserve the original answer/assessment source text and evidence
budget. New header metadata is persisted but not duplicated in model context.
Current retrieval builds it from stored extraction, without reindexing. Older
serialized PDF evidence defaults to empty header spans; it is not backfilled.
Parser associations and source-valid locations do not establish semantic support.

## Frozen component comparison

[frozen-manifest.json](frozen-manifest.json) identifies baseline commit `8181bd3`
and immutable inputs. The baseline implementation copies are verified against
that commit. [compare.py](compare.py) reuses 32 frozen packed contexts, the original
five-PDF extraction/index snapshot, three actual planned assessment responses,
and six historical generation inputs. No retrieval, planning, assessment or
generation model is rerun.

[comparison.json](comparison.json) retains per-case source/context checks,
before/after normalized references and full generation messages, input token
estimates, input/code hashes and all 20 required metric statuses. Selection and
semantic judgment are not rescored. The sales regression now displays the exact
period/date passages `p1` and `p2` as explicitly attached context for selected value
passage `p6`; the original selections remain `p6` and `p28`.
All 32 answer and annotated assessor contexts are identical before/after, and 983
exact source-span/page checks pass. Three historical assessor decisions retain
their original selected IDs, statuses and queries. Income already selected its
headers, so it gains no attachments; the conflict case gains 13 structural context
entries across three requirements. Attachment counts are not semantic quality scores.

Input-token counts use the production `cl100k_base` serialized-input counter.
They are local estimates, not provider usage or billed cost. Prompt additions
increase answer input size; evidence selection, source text and model settings
are held fixed. Quality, streaming/completion latency and production throughput
are not measured by this offline replay.

| Frozen answer input | Before tokens | After tokens |
| --- | ---: | ---: |
| Sales / single | 3,951 | 4,071 |
| Sales / planned | 4,104 | 4,291 |
| Income / single | 3,949 | 4,069 |
| Income / planned | 4,072 | 4,253 |
| Apparent conflict / single | 5,151 | 5,271 |
| Apparent conflict / planned | 3,740 | 3,933 |

The six-input mean increases from 4,161.17 to 4,314.67 tokens (+153.5).
All six remain below the 16,384-token planned answer input cap. This is not a
claim that every possible document/question fits that cap.

## Checks and retained failures

Each invocation has an append-only JSON record containing its command, baseline
commit, file hashes, duration, counts, raw log and complete metric inventory.

| Check | Result | Record |
| --- | --- | --- |
| Initial generation regression | 11 passed, 1 failed | [record](generation-tests-1.json) |
| Corrected generation regression | 12 passed | [record](generation-tests-2.json) |
| Scoped backend checks | 81 passed | [record](scoped-backend-tests-1.json) |
| Full backend suite | 752 passed, 1 skipped | [record](backend-tests-1.json) |
| Evidence-panel component tests | 4 passed | [record](frontend-tests-1.json) |
| Frontend type check and build | Passed | [record](frontend-build-1.json) |
| PDF browser lifecycle | 1 passed | [record](browser-tests-1.json) |
| Initial frozen comparison | Failed metadata-equality assertion | [record](comparison-1.json) |
| Corrected frozen comparison | Passed all comparisons | [record](comparison-2.json) |

The first generation test reconstructed a historical source without its document
identity labels, so its context-equality assertion failed. Restoring those saved
labels corrected the fixture; the failed attempt remains intact. The initial
comparison assertion likewise omitted the intentional new `source_number` metadata;
its failure is retained in [comparison-1.log](comparison-1.log). Invariant selected
IDs, quotes, offsets and verdicts are compared separately from additive metadata.

The full backend run reports 25.97 seconds in pytest. It retains two existing
dependency deprecation warnings, concerning Starlette's portal alias and Docling's
OCR setting. The skipped live test is not run to fill offline metric fields.
Browser verification uses real local HTTP/storage and mocked providers. It checks
headers/dates, reload, PDF navigation, deletion and historical text preservation.
The temporary browser servers exit with the test runner.
The final staged review retains whitespace warnings from raw pytest/Vitest logs;
source and documentation formatting checks pass with those immutable logs excluded.

Codex inspected the [assessment screenshot](browser-1/pdf-PDF-upload-page-links--ab1fc-fter-deletion-planned-true-/citation-context.png):
selected values and attached periods/dates are displayed separately with an
application-added label. This is UI inspection, not human semantic review.

## Remaining limits

Final citation completeness is still prompt-dependent. The regression deliberately
returns the original uncited bullet unchanged, proving absence of silent repair
rather than improved model compliance. The historical final-answer scores and raw
assessment decisions remain unchanged. A later complete-feature live acceptance
can measure the effect using the same frozen questions and review protocol.
Dense-table extraction omissions and broader v2 acceptance remain unresolved.
Passing these checks does not authorize a merge into `main`.
