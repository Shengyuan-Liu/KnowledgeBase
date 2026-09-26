# v2 PDF Parser Selection and Adapter Verification

Date: 2026-09-26. Branch: `v2`. Base: `c514062238a9f52cd3f5138ced82171eff29620d`.
Scope: standalone parsing/provenance and development comparison, not upload,
retrieval, answers, paid evaluation or feature acceptance. No merge was performed.

## Decision and Quality Review

Select Docling 2.130.0 with Heron layout, TableFormer V1 accurate, CPU/4 threads,
OCR and enrichment disabled. It supplies ordered items and page/character
provenance, recovers sampled company-table relationships, and handles normal
column flow better than the tested default pdfplumber extraction. V2 table models
did not resolve the hard tables. This is a bounded development decision, not proof
of general superiority. pdfplumber is not an application fallback.

Reviewer: **Codex, a model, not a human**. Original pages were rendered using
Poppler and inspected against retained output. The first four documents cover
seven reviewed pages; the Apple supplement adds one. Review includes text order,
selected facts, table headers/values/units, omissions and physical page mapping.
Labels are incomplete and development-only. No exhaustive character/cell fidelity
score or held-out acceptance is available.

| Checkpoint | pdfplumber defaults | Selected Docling V1 | Docling table V2 |
| --- | --- | --- | --- |
| Paper page 2 columns | Fail: alternating columns | Main column sequence retained; footnote interrupts continuation | Same layout behavior |
| Paper page 1 abstract fact | Text is interleaved with adjacent content | 80863 pages / 11 classes retained | Same layout behavior |
| Paper page 1 caption/order | Figure-region text mixes into body | Caption has missing spaces; right column precedes abstract | Same layout behavior |
| Lecture page 3 text | Readable native text | Required-book and guest-lecturer facts retained; some names lose spaces | Same layout behavior |
| Lecture screenshot | No OCR | Screenshot omitted; adapter reports picture limitation | Same omission |
| Dense report table | Sample Alabama values retained in table output | Fail: most cells dropped; 2x2 predicted grid | Fail: large grouped cells and wrong relationships |
| Report notes/disclaimer | Retained | Retained; not falsely attached to inferred cell values | Retained |
| Technical table | Values in text; no table detected | Partial: values retained but rows grouped and CPU label misplaced | Fail: values missing and relationships wrong |
| Cross-page paragraph | Separate page text | One paragraph with two page provenance spans | Same provenance behavior |
| Apple company table | Values retained; fragmented column grid lacks integrated period headers | Reviewed period headers, values and units correct | Not run |

Raw comparisons are in [attempt-1](attempt-1/run.json),
[attempt-2](attempt-2/run.json), and the [Apple supplement](apple-1/run.json).
Each contains unmodified Docling JSON/Markdown and pdfplumber text/table JSON.
The corpus [manifest](../../materials/pdf-v2/manifest.json),
[annotations](../../materials/pdf-v2/annotations.json),
[Apple annotations](../../materials/pdf-v2/apple-annotations.json), and
[annotation correction](../../materials/pdf-v2/annotation-corrections.json)
retain source identity and review expectations. The first comparison script was
later extended for V2/Apple; recorded script hashes distinguish each invocation.

## Performance Observations

One sequential conversion per document/configuration, with no statistical repeat
runs. Values below are wall seconds for extraction and saving its output. First
Docling conversions include model loading and, for the initial configurations,
asset fetching; do not compare those values as warm parser throughput. There is
no queue load or paid provider call. Model load/download time was not isolated.

| Compared pages | pdfplumber, initial run | Docling V1 | Docling V2 |
| --- | ---: | ---: | ---: |
| Paper 1-2 | 0.363 | 22.668 (first) | 7.453 (first) |
| Lecture 2-3 | 0.032 | 0.589 | 0.579 |
| Dense report 1 | 0.100 | 13.242 | 4.483 |
| Technical report 4-5 | 0.056 | 0.852 | 0.765 |
| Apple 1, separate process | 0.126 | 4.175 (first, cached assets) | Not run |

The final adapter was also run with `HF_HUB_OFFLINE=1` against original complete
files: Apple **4 pages**, 8.580 s including first model load; technical report
**9 pages**, 3.779 s with loaded models. Construction/model hashing took 0.259 s.
The process peak RSS was 3,680,927,744 bytes on macOS (process peak, not a per-model
allocation or steady-state estimate). These smoke tests verify execution and
slicing for all pages; visual review remains limited to the pages above.
[Timings](adapter-2/timings.json) and full immutable extractions retain evidence.
Each timing cell has n=1, so its mean, P50 and P95 are identical and not a useful
estimate of a latency distribution. Complete measured summaries, limitations and
all policy metrics are in [metrics.json](metrics.json).

## Offline Verification and Failed Attempts

- `tests-1`: 83 passed, 2 failed. Provenance spans include original list markers,
  but sanitized text removes them. Fixed by using `orig`; retain the failed log.
- `tests-2`: 86 passed after that fix.
- `tests-3`: **97 passed**, including TXT/Markdown parsing, structural/parent-child
  chunks, source locations and CLI regressions. PDF tests cover frozen outputs,
  physical pages, box origins, tables, immutable revisions, warnings and partial
  conversion rejection. Two upstream deprecation warnings remain nonfatal.
- `smoke-1`: adapter conversion produced an extraction, but the harness assumed
  three Apple pages. The original has four. Corrected the harness to use the frozen
  manifest; the failed attempt and saved extraction remain unchanged.
- `smoke-2`: both full-file adapter checks passed (13 pages). No provider calls.

Commands, code hashes, counts, durations and failures are retained in the matching
JSON/log pairs. The generic smoke wrapper initially labeled all RAG metrics not
applicable; the authoritative parser-stage/reliability scope correction is retained
in `metrics.json`, without overwriting either original record. Zero pytest counts
in smoke records mean no pytest runner was used, not zero exercised documents.

`verify_parser.py` reproduces full-file offline checks with an explicit model
asset path. Unit tests use saved Docling records without loading models. Default
installs may skip `tests/test_pdf.py`; verification here installed the `pdf` extra.
The optional dependency changes the locked transitive Typer and websockets versions;
CLI tests pass. No application configuration, credentials or existing index changed.

## Remaining Work

Dense/merged-table fidelity, first-page ordering and spacing failures remain
visible. Warnings do not automatically diagnose bad cells. Stage 2 still needs
assets/storage/upload, table-aware chunking, persisted locations and a page viewer.
No end-to-end PDF RAG quality, citation support, ingestion lifecycle, load capacity,
printed-label extraction or paid provider metrics are claimed.
