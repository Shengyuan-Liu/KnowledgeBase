# Dense table extraction: frozen offline comparison

The [gold annotations](gold.json) are frozen before the acceptance comparison.
A Codex assistant manually transcribed the original rendered first page of
`background-checks.pdf`; the reviewer is a model, not a human. The gold values and
header associations were not copied from parser output. No parsing, model calls,
or tests were run while creating these annotations.

The source is the unchanged PDF identified in the
[corpus manifest](../../materials/pdf-v2/manifest.json). Its SHA-256 is
`4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407`.
The [original rendering](../../library-runs/20260927-v2-pdf-live/source-review/background-checks-1.png)
is the visual reference. Physical page 1 is `page_index` 0. The printed footer
`Page 1 of 205` does not change the frozen fixture's one-page physical extent.
The boxes in the gold file are approximate manual localization aids, not exact
cell outlines or annotations suitable for coordinate-overlap accuracy claims.

## Scope and controls

The observed failure is the loss of Alabama's Permit **18,870**, Handgun
**23,022**, Long Gun **22,650**, and Totals **71,137** values. Freeze all 25 header
paths and all 25 positions in each Alabama, Alaska, and Arizona row to catch
shifted cells and repeated-header confusion. These labels cover 66 nonblank
numeric cells, six blank cells, and three state labels. They do not label the
remaining state rows or the footer totals.

The two Rentals cells are visibly blank in each annotated row. Preserve their
positions and distinguish blanks from the literal zero values elsewhere in the
table. Do not infer a zero from the footer or fill a missing cell from arithmetic.
The ungrouped Handgun column and `Pre-Pawn > Handgun` are different fields;
the same applies to repeated labels under the other printed group headings.
There is no printed parent heading named `Base` above Permit through Admin.

Keep the original [dense-table question and its facts](../../library-runs/20260927-v2-pdf-live/frozen-cases.json):
the question requests four Alabama values and separately asks whether the
statistics represent firearms sold. The title, November 2015 date, and disclaimer
are explicit controls. The disclaimer must still distinguish background checks
from sales and retain the absence of a one-to-one correspondence. A parser-only
comparison measures whether that evidence survives; it does not measure a newly
generated answer.

Use these existing development annotations as regression controls for the other
four corpus documents; do not invent new labels from candidate output:

| Document | Frozen controls |
| --- | --- |
| `doclaynet.pdf` | [Parser annotations](../../materials/pdf-v2/annotations.json): `paper-order`, `paper-fact`, `paper-caption` on physical pages 1–2. |
| `ml-lecture.pdf` | [Parser annotations](../../materials/pdf-v2/annotations.json): `lecture-text`, `lecture-image` on physical pages 2–3. Native text and the disclosed omission of screenshot content remain distinct. |
| `docling-report.pdf` | [Parser annotations](../../materials/pdf-v2/annotations.json): `technical-table`, `cross-page` on physical pages 4–5. Preserve merged benchmark headers, values, qualifiers, and the cross-page prose association. |
| `apple-fy24.pdf` | [Frozen facts](../../library-runs/20260927-v2-pdf-live/frozen-cases.json): `apple_sales_q`, `apple_sales_y`, `apple_units`, `apple_income_q`, `apple_income_y`; [original page 1](../../library-runs/20260927-v2-pdf-live/source-review/apple-fy24-1.png) and [reference audit](../../library-runs/20260927-financial-citation-acceptance/assessment-reference-review.json) retain period/date and units associations. |

These are reused development controls, not a held-out sample. Do not describe
uninspected pages, rows, diagrams, formulas, or OCR behavior as accepted.

## Fixed comparison and scoring

Compare the baseline and candidate on the same source bytes and frozen gold.
Save the baseline before replacing it, along with candidate outputs, parser and
model revisions, resolved settings, code versions, source hashes, errors, and
timings. Keep settings fixed except for the declared component change. If a
historical extraction is reused, disclose any version or setting difference;
do not present it as a fresh timed baseline. Preserve failed attempts and do not
revise the gold after inspecting an experiment result.

Score cell text after trimming outer whitespace and collapsing internal
whitespace runs to one space. Preserve digits, commas, signs, punctuation,
asterisks, and case. Normalize each header-path component separately. A string
match elsewhere in the table is insufficient: the value must have the correct
state row, complete parent/child header path, and physical page association.

Score blank preservation separately. An explicitly located blank may use null
or empty/whitespace-only text, but an absent column does not count as a blank.
Check all six merged parent groups, with zero-based, end-exclusive column spans
recorded in the gold. A flattened header that loses the parent relationship
does not pass even if each header word occurs somewhere in the extraction.

Report the following denominators separately rather than combining them into
a token-presence accuracy score:

- 66 nonblank numeric cells, six explicit blanks, and three state labels.
- 25 complete header paths and six merged parent spans.
- Four original Alabama table facts, each linked to its actual row and field.
- Title, report date, and disclaimer controls, including the sales distinction.
- Joint exact success for each of the three full annotated rows.
- Each applicable existing regression control for the other four PDFs, including
  source identity and physical-page mapping.

For a scoped pass, every annotated value, blank, header path, and required
association must be retained, and the selected regression controls must show no
new failure. Report baseline failures that remain separately from regressions.
Inspect the actual reconstructed rows and merged headers; valid spans alone do
not establish semantic association. Do not claim correctness for unannotated
rows or general dense-table accuracy from these three rows.

## Evidence and measurement

Keep all new artifacts in this run directory, append-only, following the
[measurement policy](../../measurement-policy.md). Record the full metric inventory
with measured values or explicit `not_applicable` / `unavailable` reasons. Record
offline command, scope, code version, duration, pass/fail/skip counts, and failures.
For extraction experiments, disclose device, concurrency, model-loading/cache
state, and whether startup is included in timing. Keep extraction quality and
performance separate.

This scope does not authorize paid answer generation or a full RAG evaluation.
Retrieval quality, answer quality, streaming latency, provider billing, and
production throughput are not measured by an offline parser comparison. Mark
those metrics accordingly instead of running paid calls merely to fill fields.
Any later live feature acceptance requires its own frozen protocol and records.
Passing these checks does not authorize a merge into `main`.
