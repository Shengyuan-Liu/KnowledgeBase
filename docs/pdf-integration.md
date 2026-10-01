# PDF Upload, Retrieval and Original Pages

Status: v2 PDF integration is implemented and its scoped functional closeout is
recorded in the [release summary](v2/release-summary.md). Upload, original-page
navigation and saved evidence after deletion pass both real and controlled browser
checks. Parser fidelity remains limited; prior failed comparisons are preserved in
[development history](v2/development-history.md). User acceptance and merge remain
the user's decision.

The closeout also retains exact previous-page headers and units for the observed
adjacent currency-row table continuation. Original extraction stays immutable and
these evidence-only changes do not require reindexing. This is not a guarantee for
arbitrary multi-page or merged tables.

## Use

Install and download local parsing weights once, from the repository root:

```bash
uv sync --locked --extra pdf
uv run --locked --extra pdf docling-tools models download layout tableformer --output-dir data/pdf-models
npm --prefix frontend ci
make app
```

`PDF_MODEL_DIR` defaults to `data/pdf-models`; configure it in the ignored `.env`
when using another location. Weights are loaded lazily and shared sequentially.
Normal startup and uploads do not download models. `make app` and `make api`
include the PDF extra. Existing TXT/Markdown data needs no reindexing.
Existing PDF entries retain their saved extraction. Upload the original PDF again
to apply a newer parser and build fresh chunks and indexes; previous answer
snapshots keep their historical evidence.

Upload a digitally generated PDF, wait for Ready, then ask a question. The library
shows the physical page count and extraction notices. Open an answer citation,
then select **Open page N**. The local PDF.js viewer renders the corresponding
original page, supports previous/next navigation, and offers the original download.
Its worker is bundled locally; opening a page requires no external viewer service.
Page numbers are one-based physical positions, not printed page labels. The viewer
does not yet highlight boxes or provide a selectable text layer.

## Data and Lifecycle

Original bytes are stored at `DATA_DIR/originals/<generated-file-id>.pdf`.
The additive `pdf_sources` SQLite table retains the immutable extraction, original
hash, extraction revision, warnings and resolved indexing settings. Existing
`document_sources` records and their TXT/Markdown constraint remain unchanged.
Parser/model identities and page geometry are part of the extraction revision.

Only ready files participate in retrieval or original delivery. Failed uploads
remove vectors, PDF assets and extraction records where cleanup succeeds; failures
remain visible and deletable. Startup recovers interrupted processing files.
Deletion first removes retrieval eligibility, then vectors, original bytes and
SQLite source/index records. A failed cleanup retains a retryable failed record.
Completed conversation snapshots retain excerpts, table context and PDF locations
after deletion, while original-page links become unavailable.

`GET /api/files/{file_id}/original?revision={revision_id}` serves an inline PDF with
byte-range support and `Cache-Control: no-store`. A mismatched revision returns
409; missing, deleted or non-ready originals return 404. File-list responses add
`page_count` and `extraction_warnings`; answer sources add nullable `pdf` metadata.
Synchronous answers, streaming sources, completion events and saved history share
the same evidence fields. PDF sources have no invented line numbers.

## Chunking and Evidence

PDF ingestion uses structural parent-child chunks with the configured parent and
child token limits, even when TXT/Markdown selects an experimental strategy.
Canonical chunks remain exact extraction slices. Oversized tables split on rows
where possible; a row exceeding the token limit splits further. Cell row/column
spans remain attached to supplied evidence.

After structural chunking, a PDF parent containing only headings joins the next
parent when that parent has body content, both lie wholly on the same physical
page, and the combined exact slice fits the original parent token budget. A
running header/footer alone does not count as body content. This addresses a
lecture title hit that previously omitted its immediately following learning
section. It does not infer nested heading levels or merge all text on a page.
Child text, IDs, offsets, heading paths and embedding inputs stay unchanged;
parent IDs/links and context spans can change. New PDF indexing records carry
`pdf_parent_context: adjacent-heading-body-v1`. Existing PDF entries need
reindexing (re-upload through the current API) to receive these new parent links;
saved answer snapshots retain their original evidence. See the
[offline comparison](../evals/check-runs/20260929-pdf-heading-context/README.md).

Before evidence packing, add separately located column headers, intersecting row
headers, and parser-associated captions/notes. Also retain an immediately preceding
paragraph when it shares the table's heading path and first physical page, excluding
running page headers/footers. This `preceding_text` supplement preserves nearby
units such as the financial statement's `(In millions, ...)` without labeling
the paragraph as a verified semantic unit definition. These carry their own source spans
and physical pages; they are not inserted into the canonical body slice. All
metadata, warnings and supplementary text count toward the actual context budget.
The diagnostic context format is `source-metadata-pdf-v2` when PDF hits are present.
Table coordinate JSON uses compact separators, retaining every cell tuple and
its canonical bounds, including empty cells and merged headers. Source text,
supplements, warnings and page metadata keep their existing representation.
The default packer defers parents intersecting PDF tables until it has tried
the selected children. It then attempts each whole table parent in selected-rank
order, replacing its siblings only when every other retained source still fits.
This also protects a selected table row from expansion of an earlier notes hit.
Non-table parent behavior and the `parent_first` control are unchanged.
Text already inside the excerpt or linked as a caption/note is not repeated as
preceding text. Other unassociated units/notes remain ordinary prose. Oversized
evidence can be excluded rather than silently exceed the budget. These retrieval-time
table supplements do not change stored extraction revisions or chunks and require
no reindex. The ingestion-time heading-parent grouping above requires new parent
records. Historical snapshots keep the evidence originally supplied.

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `services/pdf.py` | Lazily load and serialize use of the local converter |
| `storage/pdf_assets.py` | Save, locate and delete originals by generated identity |
| `storage/models.py`, `operations.py` | Persist extraction revisions and read common source contracts |
| `services/files.py` | Coordinate parsing, indexing, ready state and cleanup |
| `rag/pdf_evidence.py` | Map exact evidence spans and locate separate table context |
| `rag/pdf_chunking.py` | Join bounded, same-page heading/body parents while preserving child content |
| `rag/chunking.py`, `retrieval.py`, `packing.py` | Preserve row boundaries, attach provenance and budget context |
| `PdfViewer.tsx`, `EvidencePanel.tsx` | Open the cited original page and retain historical source display |

## Verification and Limits

The [integration run record](../evals/check-runs/20260926-pdf-integration/README.md)
retains contract tests, browser checks, failed attempts and one original-byte local
lifecycle diagnostic. The original paper, lecture and report corpus and its parser
review remain linked from [PDF parsing](pdf-parsing.md).

The dense-table repair covers three labeled development rows. Other dense tables,
the technical report's merged rows, spacing and reading-order limits remain unverified
or unresolved as detailed in [PDF parsing](pdf-parsing.md).
Ready means supported extracted content was indexed, not that every original
element was faithfully understood. OCR, visual chart/figure interpretation and
formula understanding remain excluded. Local diagnostic timings use mocked
embeddings and answers; they do not establish answer quality or production latency.
