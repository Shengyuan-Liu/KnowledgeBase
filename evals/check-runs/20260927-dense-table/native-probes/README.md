# Native ruled-table probes

The narrow candidate recovers all independently annotated cells in three state
rows of the observed collapsed table. This is an offline extraction result, not
production integration, held-out parser accuracy, or a RAG acceptance result.

## Result

| Check | Frozen collapsed table | Native candidate |
| --- | ---: | ---: |
| Correct numeric cells with row and header association | 0/66 | 66/66 |
| Explicit blank cells with row and header association | 0/6 | 6/6 |
| Correct row labels | 0/3 | 3/3 |
| Complete header paths | 0/25 | 25/25 |
| Merged parent header spans | 0/6 | 6/6 |
| Completely correct annotated rows | 0/3 | 3/3 |

[The detailed comparison](review-1-result.json) retains every observed and expected
cell, header path, native bounding box, source hash, and physical page. The
[independent gold](../gold.json) was transcribed from the original rendered page
by another Codex model reviewer, not a human. It was frozen after the initial
exploratory variants, but before the extended candidate and formal comparison.
It covers Alabama, Alaska, and Arizona only. The source table's native title,
date, and complete disclaimer phrases also survive native text extraction.

## Smallest observed method

1. Consider only an existing collapsed Docling table (`rows <= 1` or
   `columns <= 1`) on one physical page. Crop to its existing table rectangle.
2. Let pdfplumber find native vertical rules and text-derived horizontal
   boundaries with `vertical_strategy="lines"`, `horizontal_strategy="text"`.
3. Keep the native vertical rules. Pass the resulting horizontal y coordinates
   as explicit horizontal lines, spanning the crop width. This recovers the
   first column without a document-specific tolerance or x coordinate.
4. Preserve the resulting native cell rectangles, merged spans and explicit
   blank cells. Do not duplicate a merged parent label into every leaf cell.

[The probe implementation](extend_probe.py) contains no state names, numeric
answers, fixed column count, or source-specific coordinates in this extraction
rule. The resulting table has 62 geometric rows and 25 columns. It includes
separate full-width title and date rows, two empty rows, the merged group headers,
the leaf headers, and the data rows. Integration must keep title/date as context
and must not turn them into every column's parent header.

## Retained alternatives and controls

- [Default lines/text](initial-1/background-checks-page-1-lines-text.json)
  recovers the numeric columns but drops State / Territory: horizontal text edges
  start inside the outer left frame, so that frame has no intersections.
- [Default lines/lines](initial-1/background-checks-page-1-lines-lines.json)
  keeps all 25 columns and merged geometry, but combines groups of five states
  into physical horizontal bands. Its default grid also extends into footnotes.
- [Cropped lines/text](extended-1/cropped-lines-text.json) still loses the first
  column. [Extended text rows](extended-1/extended-text-rows.json) fixes this
  observed geometric cause while retaining parent and leaf header spans.
- Unrestricted lines/text creates spurious Apple and DocLayNet tables. The
  [frozen corpus gate](extended-1/summary.json) selects only the collapsed
  background-checks table: all four Apple tables, two technical-report tables,
  and five paper tables remain ineligible; the lecture has no tables.

This gate is a narrow response to the observed failure, not a general table
quality detector. A production candidate should additionally require usable
native vertical rules, a complete leaf-header band, and aligned single-line
body rows. Native punctuation differs from the visual page in some unannotated
rows, including California's thousands separators; no quality claim is made for
those rows or the footer totals. Canonical extraction offsets, chunking, embedding,
retrieval and answer behavior have not been exercised by these probes.

## Reproducibility and measurement

The bundled runtime supplied pdfplumber 0.11.9, pdfminer.six 20251230,
pypdfium2 5.13.0 and Pillow 12.3.0. No package was installed and no provider was
called. Experiments used one CPU process, no warmup, uncontrolled OS caches,
no retry and no configured subprocess timeout. All eight parser variants
completed; a completed extraction can still fail the quality goal.

Invocation records retain exact commands, code and source hashes, environment,
durations, and all 20 required metric statuses:
[initial](initial-1.json), [extended](extended-1.json), and
[gold comparison](review-1.json). [Aggregate measurement](measurement.json)
separates parser quality from RAG metrics. Per-stage durations include local
artifact serialization where performed inside the timed stage; these heterogeneous
exploratory variants are not a production latency comparison. The review command's
duration is offline comparison time, not parser latency.
The first report-link review failed because it checked its own measurement output
before creating it; that attempt remains in `report-review-1.json`. The corrected
review is retained separately.

Raw characters, words, edges, intersections, table rectangles and extracted cells
remain in the new run directories. Historical fixtures and the user library were
not modified. Any production extraction change requires a new revision and fresh
chunks, lexical index and embeddings from the original PDF.
