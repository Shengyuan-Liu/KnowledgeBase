# File Ingestion

`FileService` in `knowledgebase/services/files.py` owns upload transactions,
indexing, interrupted-upload recovery and deletion. API, CLI and evaluation
entry points construct it from the shared [Settings](configuration.md).

## Models and responsibilities

- `File` represents TXT, Markdown and PDF. Its `type` is `txt`, `md` or `pdf`.
  Parsed text and `SourceBlock` records live on that same object. Pages, regions,
  tables and parser identity are optional PDF data, not alternative file models.
- `Chunk` represents flat, parent and child spans. Every span has a `chunk_id`;
  `type` identifies its role and a child's `parent_id` refers to its parent.
  `ChunkBatch` is a plain dataclass grouping parent and indexed-span lists.
- `DocumentParser` validates upload bytes and selects parsing by `File.type`.
- `DocumentChunker` owns splitting settings. Pure splitting algorithms remain
  independently testable; this class selects and configures them.
- `FileService` shares the parser, chunker, embedding client, vector store,
  original-file storage and session factory across its operations.

`File` and `SourceBlock` are immutable snapshots. Use `model_copy(update=...)`
when attaching new metadata; their contents are independent of database sessions.

## Workflow

1. Check the extension, UTF-8/nonempty text for TXT/Markdown, or the PDF signature
   and configured PDF resources. Invalid uploads create no file record.
2. Commit a new `processing` file ID. Repeated filenames still get distinct IDs.
3. Parse the source and split it. PDF uses parent-child splitting with table-row
   boundaries and heading context. Text uses the configured strategy. The default
   is 512-token children, 1536-token parents and `cl100k_base` counting. Structural,
   character and semantic strategies remain available for TXT/Markdown.
4. Embed indexed spans. Parents provide retrieval context and are not embedded.
5. Persist source content, indexing settings, chunk metadata and links; write
   vectors; mark the file `ready`. SQLite writes share one transaction, while
   SQLite, Chroma and original PDF assets do not share a transaction.

TXT/Markdown retain the exact decoded source in SQLite. PDF also retains original
bytes for page navigation. A processing failure marks the file `failed` before
cleanup, then removes its vectors, chunks and original PDF. Failed cleanup remains
visible and can be retried by deleting the file. Startup calls `FileService.recover`
under the data-directory ownership lock; it does not resume embedding jobs.

## Usage

```python
from pathlib import Path

from knowledgebase.services.files import FileService
from knowledgebase.services.pdf import LocalPdfParser
from knowledgebase.storage.pdf_assets import PdfAssets

files = FileService.from_settings(
    settings, sessions, embeddings, store,
    assets=PdfAssets(settings.data_dir),
    pdf_parser=LocalPdfParser(settings.pdf_model_dir),
)
path = Path("notes.md")
file_id = files.ingest(path.name, path.read_bytes())
files.delete(file_id)
```

Direct offline callers can inject a `DocumentChunker` and test doubles through the
constructor. No extra configuration model or schema per parser is required.
Changing settings affects new uploads only; existing records need no migration
for this model refactor. The established SQLite tables and PDF revision payload
remain compatible with prior v2 records.

See [PDF setup](pdf-integration.md), [file API](file-api.md),
[chunk storage](document-storage.md) and [deletion](file-deletion.md).
The [refactor verification](../evals/check-runs/20261001-unified-file-oop/README.md)
records offline regressions and matched frozen-data comparisons; it makes no new
live answer-quality or performance claim.
