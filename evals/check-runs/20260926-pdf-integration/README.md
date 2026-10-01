# PDF Integration Verification — 2026-09-26

Scope: connect the frozen PDF adapter to upload, persistence, parent-child
retrieval, budgeted table context, answer snapshots and original-page viewing.
Base commit: `9165108`; every command JSON also retains code-file hashes for the
uncommitted implementation at that invocation. This directory is append-only.
No feature acceptance, merge or general quality improvement is claimed.

## Final Checks

| Record | Result |
| --- | --- |
| `backend-3` | 615 passed, 1 skipped; 23.04 seconds reported by pytest |
| `frontend-2` | 44 passed across 6 files; 1.45 seconds reported by Vitest |
| `browser-3` | 13 passed; 23.5 seconds reported by Playwright |
| `build-4` | TypeScript and Vite production build passed |
| `local-1` | Real original-byte parsing, indexing, retrieval, restart, deletion and preserved history passed |

Each named `.json` contains command, device, timestamp, wall time and metric
inventory; `.log` contains raw output. The explicit
[measurement supplement](measurement-supplement.json) corrects generic metric
applicability and the original Vitest count parser (44 tests, not 50). No raw
record was overwritten. One optional live-provider test is skipped; existing
Starlette/Pydantic deprecation warnings remain visible.

The browser server uses the frozen real Apple extraction, real original PDF bytes,
SQLite/Chroma and mocked provider responses. Assertions cover rendered canvas,
physical page selection, next/previous navigation, refresh and deleted-original
history. [Final viewer](browser-3-artifacts/pdf-viewer.png) and
[evidence panel](browser-3-artifacts/pdf-evidence.png) were visually inspected by
Codex: the page is readable, the physical page agrees with the link, and controls
remain visible. Screenshots do not establish semantic correctness of mock answers.

## Local Original-byte Diagnostic

`local_lifecycle.py` runs one sequential Apple FY24 PDF through the actual local
parser and temporary library. Embeddings are constant two-dimensional mocks;
the answer is a fixed placeholder. No provider calls occur. The
[details](local-1-details.json) retain source hash, parser/model hashes, complete
extraction, candidates/ranks, exact supplied evidence, exclusions, context tokens,
placeholder answer and stage observations.

- Four pages; local CPU, four Docling threads; fresh parser, local weights.
- Upload-to-ready: **10.074 s**, including **10.012 s** parsing/initial model loading.
- Retrieval: **0.0148 s**; deletion: **0.00626 s**.
- Temporary storage before deletion: **5,479,284 bytes**, including original,
  SQLite/WAL and Chroma. Local compute billing is unavailable.
- One sample per timing; mean/P50/P95 are identical to that sample and are not
  population estimates. No queue wait or load workload; concurrency is one.
- Original identity, ready evidence, page provenance, reopen, deletion and exact
  historical evidence retention all passed. Re-upload is the update path.

Retrieval relevance/coverage annotations, actual answer quality, first-answer-delta
latency and provider performance are unavailable or not applicable as detailed in
the supplement. Total test time is not answer latency. A stage-1 PDF application
baseline does not exist, so no PDF quality gain is asserted. The same frozen
Apple extraction is used in table-header/budget regression tests; existing
TXT/Markdown behavior is covered by the complete offline suites.

## Preserved Failed Attempts

- `integration-1`: one new SSE test omitted `request_id` and incorrectly parsed
  event/data frames. Corrected test passes in `integration-2` and later suites.
- `backend-1`: six failures exposed outdated schema/CLI response expectations and
  an unintended TXT source cleanup change. Updated the contract expectations and
  limited extraction cleanup to PDFs, preserving existing TXT recovery behavior.
  `backend-2` passes all 79 affected tests; `backend-3` passes the full suite.
- `browser-1`: native PDF popup remained blank in the browser. Retained trace and
  error context in `browser-1-artifacts`; bundled PDF.js rendering replaces it.
  `browser-2` and `browser-3` pass.
- `build-2`: installed PDF.js requires an object argument to `getDocument`.
  Corrected call passes `build-3` and `build-4`.

Known parser table-data, row-association, spacing and reading-order failures from
the [parser selection](../20260926-pdf-parser-selection/README.md) remain open.
Only parser-associated headers/captions/notes are attached; unrelated unit text
is not inferred. OCR, figure interpretation and formula understanding are excluded.
The viewer provides page rendering, navigation and download, without box highlights
or a selectable text layer. No paid or live-answer acceptance evaluation was run.

The final staged whitespace check (`whitespace-1`) reports whitespace in preserved
raw tool logs and the browser error artifact. These outputs remain byte-for-byte
unchanged. The source/document check (`whitespace-2`) excludes those generated raw
artifacts and passes. This is a formatting exception for append-only evidence.
