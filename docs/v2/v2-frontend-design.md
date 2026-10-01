# KnowledgeBase v2 Frontend Design

Status: v2 Library, Chat and Evidence flows implemented and scoped browser checks
completed. See the [release summary](release-summary.md) for actual UI limits,
including the absence of a conversation picker and PDF zoom. All copy stays English.

## Library and PDF Upload

Use `Upload TXT, Markdown, or PDF` and accept the corresponding formats. Retain
Processing, Ready, and Failed states, backend validation, and deletion feedback.
Show PDF page count when known and an extraction notice when some content was
not indexed. Do not label an image-only upload as fully searchable because its
filename or a small text layer was extracted.

The core uses digital PDFs; OCR is outside v2. Communicate that limitation
directly when applicable, for example `This PDF requires OCR,
which is not supported in this version.` Mixed documents need a visible notice
about affected pages when identifiable. Do not promise percentage completeness
without a measured basis.

## Evidence and Original Page

Each numbered source represents an excerpt actually supplied to answer generation.
Show filename, heading when available, and locations such as `PDF page 7 of 24`.
If a printed label exists, show it separately as `Printed page: 3`. Cross-page
evidence lists its actual pages without implying that intervening pages were used.

The evidence panel provides:

1. **Saved excerpt:** exact extracted text supplied to generation, with readable
   table content and any extraction limitation relevant to that source.
2. **Open original page:** an embedded page view while the original asset exists,
   with page navigation and zoom. The exact viewer library remains unselected.

Preserve page mapping as the required capability. Highlight regions only when
stored coordinates can be transformed reliably for rotation and zoom. Otherwise
open the correct page without pretending to know a precise word location.
Highlighting an entire block must look like block selection, not exact quotation
verification. Keep keyboard navigation and readable responsive layouts; on narrow
screens the evidence/page view can open as a separate panel.

TXT/Markdown sources continue using their existing line locations. Old snapshots
without PDF or controller metadata remain readable with missing information
labeled `Not recorded`, never fabricated.

## Retrieval Progress and Streaming

Use brief status text tied to actual controller events:

- `Planning the search`
- `Searching your documents`
- `Checking supporting evidence`
- `Searching for missing information`
- `Writing the answer`

Do not show invented percentages or private model reasoning. Progress must use
the request identity and must not create a saved answer. Stop remains available
through planning, retrieval, checking, and generation. An interrupted partial
answer stays unsaved under the existing lifecycle.

Finish retrieval before publishing numbered sources and streaming the final
answer. Source IDs remain stable for that message. Refresh restores completed
answers and saved traces without re-running retrieval.

## Answer Presentation

Use normal cited prose or a comparison table when appropriate. If some required
points remain unsupported, the answer states them explicitly, for example
`The retrieved evidence does not specify the evaluation dataset for Paper B.`
Do not upgrade this to a whole-document absence claim without supporting evidence.

The controller's `supported` assessment is not a public correctness badge. Show
remaining gaps and source-specific conflicts when meaningful; leave algorithm
settings in diagnostics rather than adding configuration to normal chat use.

## Optional Diagnostics

Extend the existing collapsed `Debug details` with compact, inspectable records:

| Detail | Presentation |
| --- | --- |
| Search requirements | Short requested points and their final support status |
| Queries and dependencies | Per-round search text and source links that identified a dependent target |
| Retrieval | Existing route scores plus separately labeled cross-query fusion ranks |
| Context | Final included evidence, deduplication, and budget exclusions |
| Termination | Recorded reason such as sufficient evidence, budget exhausted, or no new evidence |
| Performance | Available planning/retrieval/checking/generation durations and usage |

No score is presented as a probability of correctness. Missing usage or cost is
`Not recorded`, not zero. The normal view needs only useful progress and citations.

## History, Deletion, and Acceptance

After deletion, show `Original PDF deleted` and disable original-page viewing.
Keep historical excerpts, page metadata, and saved answer diagnostics. A reindexed
file must not silently replace the evidence shown for an older answer.

Verify uploads, page numbering versus printed labels, cross-page sources, table
readability, citation selection across messages, Stop at each stage, error feedback,
refresh, deletion, and TXT/Markdown regressions. Include keyboard and narrow-screen
checks and a real-provider workflow when the complete feature is ready. UI tests
establish interaction behavior; semantic answer quality has separate acceptance.
