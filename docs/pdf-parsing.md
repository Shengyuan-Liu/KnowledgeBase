# PDF Parsing and Page Provenance

Status: standalone v2 adapter implemented on `v2`. PDF upload, persistence,
retrieval and page viewing are still stage 2 work. This is not a claim of general
PDF fidelity or user acceptance.

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

`data/` is ignored by Git. Pass the model directory explicitly; application
Settings integration belongs to the ingestion stage. No credentials are required.

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
Partial conversion is rejected. No fallback parser is configured. Installing this
extra does not enable PDF uploads or import Docling in existing application routes.

## Module Responsibilities

| File / function | Responsibility |
| --- | --- |
| `knowledgebase/rag/pdf.py`: `PdfParser` | Configure the local converter, record package/model identity, parse complete PDF bytes |
| `adapt_pdf_document` | Convert ordered parser items into canonical text, blocks, geometry and warnings |
| `_table` | Serialize each cell once; preserve row/column spans, header flags, caption and footnote references |
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

The dense background-check report loses table data. The technical report table
combines thread-count rows and misassigns a CPU-label fragment. Neither table is
accepted as faithfully extracted. The paper's first page places right-column
content before its abstract, although the second-page main-column sequence is
usable. Some names, captions and headings lose spaces. Failures remain recorded.

Every table carries `table_structure_unverified`; this is a limitation notice,
not an automatic detector of which cells are wrong. Pictures and formula text
have explicit scope warnings. Pages without mapped text receive
`no_extracted_text`, without guessing whether they are blank or scanned. Valid
slices and page boxes alone never establish original-page fidelity.

Stage 2 must connect storage and page viewing and preserve table headers when
splitting oversized tables. The current chunker does not yet do that for these
PDF records. The eventual upload UI must surface extraction limitations.

## Verification

```bash
uv run --locked --extra pdf python -m pytest tests/test_pdf.py tests/test_parsing.py tests/test_structured_chunking.py tests/test_parent_child_chunking.py tests/test_source_locations.py tests/test_cli.py -q
```

Tests use frozen real output and controlled records, without model downloads or
provider calls. Without the PDF extra, PDF tests are explicitly skipped. A separate
recorded offline smoke run processes original Apple and technical-report PDF bytes
with local weights. See the [run record](../evals/check-runs/20260926-pdf-parser-selection/README.md)
for results, failed attempts, model identities and limits.

Primary references: [pipeline options](https://docling-project.github.io/docling/reference/pipeline_options/),
[model setup](https://docling-project.github.io/docling/usage/advanced_options/),
[pdfplumber API](https://github.com/jsvine/pdfplumber).
