# Unified File and Chunk Models with File Services

Baseline: `dea314a`. Scope: replace redundant Python document schemas, dispatch
file parsing by type, and give the file workflow explicit service objects.
This is subsequent v2 work; no merge is authorized by these checks.

## Delivered structure

- Six span schemas (`ChunkContent`, `Chunk`, `StructuredContent`,
  `StructuredChunk`, `ParentChunk`, `ChildChunk`) become one `Chunk`.
  `type` distinguishes flat, parent and child spans. A span's own ID is always
  `chunk_id`; only a child uses `parent_id` to reference another span.
- `FileInfo`, `DocumentSource` and `PdfExtraction` become one `File`, with
  `type="txt" | "md" | "pdf"`. PDF pages, parser identity and table locations
  are optional data on this model. Metadata endpoints omit source contents.
- `PdfBlock` and `SourceBlock` become one immutable `SourceBlock` with optional
  location/table fields. `ParentChildChunks` becomes the plain `ChunkBatch`
  dataclass; it groups spans without adding a second chunk schema.
- `DocumentParser` selects parsing, `DocumentChunker` owns splitting settings,
  and `FileService` owns ingestion, cleanup, recovery and deletion. API, CLI and
  current evaluation entry points use these objects. Pure splitting algorithms
  remain functions. Historical experiment scripts remain at their recorded API.
- File listing joins metadata in one query; line-citation construction reads
  canonical text in a batch without loading parser blocks or duplicate file
  metadata. The duplicate failed-upload/recovery cleanup paths share one method.

The schema module has 22 to 13 Pydantic model classes, plus one plain grouping
dataclass. [Physical source-line counts](code-size.json) show backend 5,876 to
5,810 lines and frontend 3,042 to 3,043: net 65 fewer product lines, including
comments/blanks and excluding tests, documentation and experiment artifacts.
This is principally an interface and responsibility simplification.

## Compatibility

Existing SQLite tables remain unchanged. Storage maps old parent primary keys to
`Chunk.chunk_id` and restores absent legacy token metadata as null. PDF extraction
hashes and revision payloads retain their established serialization. No library
migration, reindex, original-file modification or paid provider request occurred.

The Python imports and service entry points intentionally change; callers use
`File`, `Chunk` and `FileService` instead of the removed classes/free functions.
`File` and `SourceBlock` are immutable snapshots; update copies explicitly.
HTTP metadata adds `type`, preserves PDF warning/page fields and excludes text,
blocks, pages and parser records. Saved historical answer evidence remains readable.
Unified chunks additionally retain structural metadata in nested serialized
retrieval results; canonical fields and the actual model context remain identical
in the matched replay.

## Verification

| Check | Result | Record |
| --- | --- | --- |
| Backend | 854 passed; 1 opt-in live smoke skipped | [backend-final.json](backend-final.json) |
| Frontend | 49 passed | [frontend-final.json](frontend-final.json) |
| Browser lifecycle, history and citations | 21 passed | [browser-final.json](browser-final.json) |
| Frontend type checking/build | Passed | [frontend-build-1.json](frontend-build-1.json) |
| Unused imports/variables and unresolved names | Passed | [unused-final.json](unused-final.json) |
| Frozen PDF comparison | 5/5 extraction payloads/revisions and chunk sets identical | [comparison-results.json](comparison-results.json) |
| Frozen query comparison | 16/16 top-20 BM25 rankings, packed source spans, PDF evidence and rendered contexts identical | [comparison-results.json](comparison-results.json) |

The frozen workload includes financial tables, lecture slides, papers/reports
and the background-check table. It reuses existing Docling output and 16 existing
questions from the evidence-packing corpus. The identical lexical top-5 candidates
are passed through parent expansion and a 4,096-token evidence budget. This is
an offline behavior comparison, not a live answer-quality evaluation.

[Before](before-2.json) and [after](after-1.json) retain input hashes, exact chunks,
rankings, supplied evidence and context. [Measurement](measurement-2.json) records
all 20 metric statuses. Timing diagnostics describe local frozen adaptation /
chunking and lexical search / packing only, with one sequential pass per arm.
They exclude model conversion and generation and establish no speed claim.
Codex performed the equality review; no independent human quality rating is claimed.

## Retained failed attempts

- `focused-1`: 131 passed, 4 failed while adapting assertions for immutable file
  snapshots, tuple blocks, legacy SQL column projections and unified metadata.
- `backend-1`: 787 passed, 57 failed, 9 setup errors, 1 skipped. Besides legacy
  test/API expectations, this found cached service resources bypassing replaced
  cleanup dependencies and a repeated file metadata lookup. These were fixed;
  the targeted follow-up passed 164 and the final backend run passed 854.
- `unused-1`: seven imports left unused after merging types; all were removed.
- `replay-before-1`: replay harness omitted required packing options; it made no
  provider calls. `replay-2.py` specifies the same packing settings for both arms.
- `comparison-1`: compared elapsed packing time and newly retained serialization
  metadata as though they should match the old JSON byte shape. `compare-2.py`
  excludes timing and compares that metadata on full canonical chunks instead.
  It still checks exact context, ranking, canonical spans and all PDF evidence.

- `comparison-3`: repeat the same successful comparison with distinct names for
  result data and command records. The earlier `comparison-2.json` command record
  had replaced the comparison script's same-named result file. Exact before/after
  inputs remained intact; `comparison-results.json` now retains all 21 case results.

All earlier logs and failed comparison data remain here. No unresolved test
failure remains; live quality, cost and production performance were not measured.
