# OOP refactoring verification

Baseline production code: `bbd0a8d`; plan commit: `d5a1cde`.
All checks use offline providers and temporary storage. No user library, secrets,
model settings or historical evaluation artifacts are modified.

## Baseline

- `baseline`: 854 passed, 1 explicitly opt-in live test skipped.
- `freeze-contracts`: first successful snapshot, retained unchanged.
- `freeze-contracts-v2`: 1 passed; tightened identity normalization so 64-character
  source hashes remain exact. `behavior-before-v2.json` is the comparison baseline.
- `tests/test_oop_contracts.py` freezes one TXT corpus, single/planned requests,
  planned streaming, follow-up resolution, missing scope, deletion/history and
  empty-library behavior. Provider responses are fixed by the recorded test fixture.
  Stored observations include chunks, sources, ranks, budgets, model payloads,
  event order, answer snapshots and nine schemas.
- Normalization excludes keys ending in `_seconds`, `seconds`, `created_at` and
  `updated_at`; generated 32-hex identities are consistently renamed. Timing is
  not compared and mocked outputs do not establish live quality or performance.

Every command has an append-only JSON/log pair containing the full metric inventory,
code hashes, command, duration, result counts and any failure output.

Stage results and the final comparison are recorded below.

## Document processing

- `document-processing`: 170 passed, 3 failed. Two semantic fixtures still supplied
  embeddings only to FileService; one failure fixture patched the old parser module.
- `document-processing-fixes`: 28 passed, 1 failed. A broad fixture import edit also
  changed an unrelated file-status patch; restored its services import.
- `document-processing-final`: 29 passed. Corrected semantic dependency injection
  and patch locations; the frozen HTTP/prompt/history contract remains equal.

## Retrieval components

- `retrieval-components`: collection failed on a nested import indentation changed
  during the parser/chunker move. Corrected the test import.
- `retrieval-components-2`: 94 passed, 63 failed from a missing RequirementEvidence
  import in the moved plan executor; downstream API failures share that cause.
- `retrieval-components-3`: 158 passed, including reused-retriever scope isolation,
  independent/dependent plans, assessment, cancellation and frozen contract equality.
- `retrieval-consumers`: 62 passed across storage-backed retrieval, file API,
  ingestion/deletion, PDF packing and recovery.

## RAG and conversation components

- `rag-chat-components`: 155 passed, including JSON/SSE equality, cancellation,
  time budgets, binding/assessment failures and the frozen contract comparison.
- `service-reuse`: 2 passed. Two overlapping streams through one ChatService keep
  file scope, answer text and saved histories separate; request deadlines and
  cancellation do not overwrite shared model client limits.

## Bootstrap and consumer migration

- `bootstrap-api`: 20 passed and 103 fixture errors from a missing bootstrap import
  after moving provider construction. The fixture imports were corrected.
- `bootstrap-smoke`: 23 passed, including CLI overrides and frozen HTTP contracts.
- `static-components`: retained 25 findings (unused imports/locals and two missing
  bootstrap references); `static-components-2` passed after cleanup.
- `bootstrap-backend`: 848 passed, 10 failed, 1 skipped. Eight recorded assessment
  replays still called the old HopController constructor; two API fixtures patched
  providers in their old module. No failed expectation was removed.
- `bootstrap-regression-fixes`: 36 passed after migrating those call sites.
- `final-backend`: 858 passed, 1 opt-in live smoke skipped, 0 failures/errors.
- `final-browser`: 21 passed, exercising HTTP/SSE, responsive file management,
  PDF citations, history, source deletion, dependent plans and cancellation.
- `behavior-after.json` matches the normalized frozen baseline. A separate
  comparison receipt documents exact groups and schemas after code commit.

The frozen contract covers a deterministic TXT fixture, not a new live quality
benchmark. Existing PDF/rerank/dependency fixtures and their assertions remain in
the offline suite. Real-model quality, billing, production latency/throughput and
new live PDF extraction fidelity were not measured. No paid LLM evaluation ran.
Existing Starlette/Docling deprecations remain; browser logs also retain the
existing Node color-environment warnings. Tests use isolated temporary storage.

The initial read-only directory/class audit and document content review did not
execute model requests. Markdown reviews are recorded separately. The project
SDK, model, tokenizer and dependency-lock defaults remain unchanged.
