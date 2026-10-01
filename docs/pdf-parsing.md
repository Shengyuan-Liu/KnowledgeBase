# PDF Parsing and Page Provenance

Status: v2 adapter and [stage 2 integration](pdf-integration.md) implemented on
`v2`. This is not a claim of general PDF fidelity or user acceptance.

## Selection and Scope

The user requested papers, lectures and company/technical reports. Five original
files are frozen in the [development corpus](../evals/materials/pdf-v2/README.md).
The [comparison record](../evals/check-runs/20260926-pdf-parser-selection/README.md)
retains pdfplumber, Docling TableFormer V1 and TableFormer V2 outputs, including
failures. Select **Docling 2.130.0, Heron layout, TableFormer V1 accurate, four CPU
threads**. Default pdfplumber text interleaves the sampled columns; TableFormer V2
did not resolve the tested table failures. Sampled company-table cells and normal
column ordering favor this configuration, without establishing general superiority.

Digital English text, native captions and supported table structures are the
target. OCR, visual interpretation and formula understanding are disabled. Models
run locally; no provider API is called. Downloading model assets is a separate
setup step. Docling uses the MIT license; model repositories carry their own
license declarations. Package versions and model-file hashes identify the actual
code and weights in each extraction.

## Setup and Use

```bash
uv sync --locked --extra pdf
uv run --locked --extra pdf docling-tools models download layout tableformer --output-dir data/pdf-models
```

`data/` is ignored by Git. Standalone callers pass the model directory explicitly;
the application uses `PDF_MODEL_DIR` (default `data/pdf-models`). Parsing itself
requires no credentials.

```python
from pathlib import Path
from knowledgebase.rag.pdf import PdfParser

parser = PdfParser(Path("data/pdf-models"))
extraction = parser.parse(Path("report.pdf").read_bytes())
block = extraction.blocks[0]
assert block.text == extraction.text[block.start_offset:block.end_offset]
locations = extraction.locate(block.start_offset, block.end_offset)
print([(location.page_index + 1, location.bbox) for location in locations])
print(extraction.warnings)
```

Reuse a parser across sequential documents. Construction hashes local model files;
the first parse loads models. Missing assets and conversion failures remain errors.
Partial conversion is rejected. The PDF extra includes Docling and pdfplumber;
the application imports the parser on the first PDF upload.
After a successful conversion, the scoped recovery below can reconstruct a
collapsed table from native text and rules; it does not recover failed conversions.

## Collapsed Ruled Tables

The [dense-table repair record](../evals/check-runs/20260927-dense-table/README.md)
isolates an observed failure: the background-check report reaches TableFormer
with its native values intact, but structure prediction reduces the whole table
to one cell. Disabling cell matching or changing the PDF backend did not fix it.

For a **single-page table with at most one extracted row or column**, the parser
now tries pdfplumber 0.11.9 within the existing Docling table box. It uses native
vertical rules and text-row positions, extending horizontal row boundaries across
the box so that the left row-label column is included. Recovery requires one
native grid and a labeled numeric body. Rows before the first labeled row with
at least two numeric cells and a numeric majority are marked as headers. This is
a structural heuristic, not semantic table understanding.

The adapter retains merged column spans, explicit blank cells, native text and
physical-page boxes. Full-width title/date cells remain table context. It never
fills blanks with zero or synthesizes missing values. Other tables keep their
Docling output. Every recovered table has a `native_table_recovery` notice and
still carries `table_structure_unverified`.

The frozen development check now recovers all four original Alabama facts and
the complete Alabama, Alaska and Arizona rows: 66 numeric cells, six blanks,
25 header paths and six merged groups. Four other sampled corpus documents keep
identical canonical text and block geometry. These labels cover three rows of
one known failure, not every row, held-out tables, or end-to-end answer quality.
The subsequent [live replay](../evals/library-runs/20260927-dense-table-acceptance/README.md)
confirms the recovered values reach the index and retrieval candidates, but their
table metadata pushes the selected excerpt over the evidence budget. The parser
checks therefore do not imply that answers can yet use those values.

Parser identity records the recovery algorithm/settings and pdfplumber/pdfminer
versions. Changed extraction creates a new revision. Existing library entries
and historical evidence are not rewritten: upload the original again to create
fresh chunks, BM25 entries and embeddings. There is no automatic reindex endpoint.

## Module Responsibilities

| File / function | Responsibility |
| --- | --- |
| `knowledgebase/rag/pdf.py`: `PdfParser` | Configure the local converter, record package/model identity, parse complete PDF bytes |
| `adapt_pdf_document` | Convert ordered parser items into canonical text, blocks, geometry and warnings |
| `_table` | Serialize each cell once; preserve row/column spans, header flags, caption and footnote references |
| `knowledgebase/rag/pdf_tables.py`: `recover_collapsed_tables` | Reconstruct eligible collapsed numeric tables using native rules and text rows before canonical serialization |
| `knowledgebase/rag/pdf_models.py` | Frozen records with tuples for nested collections and JSON round-trip support |
| `PdfExtraction.locate` | Intersect a canonical span with all its page regions, retaining box precision |
| `PdfExtraction.source_blocks` | Return independent copies for the structural chunker; no upload or table-aware splitting integration |

## Source Contract

- `source_hash` identifies original bytes; `extraction_hash` identifies extracted
  text. `revision_id` also hashes provenance, warnings, parser settings and model
  identities. Snapshots are immutable and content-addressed.
- Page indices are zero-based physical indices. Display `page_index + 1`. Printed
  labels are unavailable and explicitly reported, never guessed.
- Boxes are `(left, top, right, bottom)` in PDF points with a top-left origin.
  Page dimensions are preserved. A block box does not imply word precision.
- Offsets are end-exclusive Python character positions in canonical text, not PDF
  byte offsets or offsets into a Markdown export.
- Canonical text uses Docling's `orig`: its provenance includes list markers that
  sanitized `text` removes. This fixes a recorded offset regression, without
  repairing upstream spacing or text-recognition errors.
- Blocks have two synthetic newlines between them. Tables serialize each cell once
  with tab/newline separators. Merged cells are not repeated into every grid slot;
  row/column metadata defines their associations. Separators are not printed text.
- Cross-page blocks retain each provenance span. Lookups return every intersecting
  region without narrowing its box to claim greater precision. Synthetic gaps may
  have no mapped location.
- Table regions remain table-level. Cell boxes have page IDs only when a single
  table page makes the association unambiguous. Caption/note references retain
  parser item identities. Notes without a parser association remain ordinary text.

## Known Limits

The dense background-check report's original loss is repaired for its three
annotated development rows; the rest of that table remains unverified. The
technical report table still combines thread-count rows and misassigns a
CPU-label fragment, and is not accepted as faithfully extracted. The paper's
first page places right-column content before its abstract, although the second-page main-column sequence is
usable. Some names, captions and headings lose spaces. Failures remain recorded.

Every table carries `table_structure_unverified`; this is a limitation notice,
not an automatic detector of which cells are wrong. Pictures and formula text
have explicit scope warnings. Pages without mapped text receive
`no_extracted_text`, without guessing whether they are blank or scanned. Valid
slices and page boxes alone never establish original-page fidelity.

The [stage 2 integration](pdf-integration.md) now connects storage and page
viewing, splits oversized tables at row boundaries when possible, preserves
separately located headers, and surfaces extraction limitations in the UI.

## Verification

```bash
uv run --locked --extra pdf python -m pytest tests/test_pdf.py tests/test_pdf_tables.py tests/test_parsing.py tests/test_structured_chunking.py tests/test_parent_child_chunking.py tests/test_source_locations.py tests/test_cli.py -q
```

Tests use frozen real output and controlled records, without model downloads or
provider calls. Without the PDF extra, PDF tests are explicitly skipped. A separate
recorded offline smoke run processes original Apple and technical-report PDF bytes
with local weights. See the [run record](../evals/check-runs/20260926-pdf-parser-selection/README.md)
for results, failed attempts, model identities and limits.

Primary references: [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
[model setup](https://docling-project.github.io/docling/usage/advanced_options/),
[pdfplumber API](https://github.com/jsvine/pdfplumber).
