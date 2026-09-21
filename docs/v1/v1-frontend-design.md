# KnowledgeBase v1 Frontend Design

## Scope

Status: planned. Extend the existing Library, Chat, and Evidence workspace using
React, TypeScript, Vite, and CSS Modules. Retain the [MVP interaction design](../mvp/mvp-frontend-design.md)
and the implemented [frontend workflow](../frontend.md).

The visible changes are Markdown upload support, source locations for parent
evidence, and optional diagnostics. Retrieval techniques remain backend concerns;
the user does not need to choose BM25, RRF, or a reranker to ask a question.

## Library and Upload

- Change the upload action to `Upload TXT or Markdown` and accept `.txt` and `.md`.
- Identify file format in the list while retaining Processing, Ready, and Failed states.
- Use backend validation results for UTF-8, empty, and unsupported-file feedback.
- Preserve deletion, retry feedback, keyboard interaction, and responsive layout.

No Markdown editor, document folder system, or document preview workspace is added.

## Evidence Navigation

Each numbered source represents one parent excerpt actually supplied to generation.
Show its filename, heading path when available, and original source location. Use
line ranges derived from the canonical text for display; character offsets remain
the precise stored location. Do not invent Markdown headings for TXT content.

The default evidence view shows the exact source excerpt as text, including Markdown
syntax where present. This avoids confusing a transformed rendering with a literal
quote. Code and table content remain readable with local scrolling as needed.
Do not render source HTML or load remote images.

Child hits may be highlighted within the parent as selection context. The entire
displayed parent is the numbered evidence; highlighting does not prove that a claim
is supported. Multiple selected children may point to one source card.

Keep source selection scoped by message ID and source number. Distinguish cited
sources from additional supplied evidence. Saved answers show their saved excerpts,
with existing deleted-source indicators. Older snapshots without heading or parent
metadata remain readable without fabricated locations or diagnostics.

## Optional Debug Details

Provide a collapsed `Retrieval details` disclosure, extending the current debug view.

| Detail | Presentation |
| --- | --- |
| Retrieval question | Show the resolved query separately from the user's original question |
| Retrieval routes | Label lexical and vector membership/rank for each candidate |
| Scores | Keep BM25, vector distance, RRF, and rerank values separately labeled |
| Selection | Show selected child-to-parent associations and parents excluded by the context budget |
| Timing | Show available retrieval, rerank, and total durations with clear labels |
| Configuration | Show the recorded strategy/model identifiers when available |

Missing values appear as `Not recorded`; do not display them as zero. No relevance
score is labeled confidence, accuracy, or a probability. Do not add retrieval
configuration controls to the normal chat flow.

## API and Streaming Impact

Keep the existing endpoints and request lifecycle. Extend shared source and debug
payloads to carry parent identity, source location, heading paths, and child traces.
The exact schema must be designed together with backend snapshots and frontend
types before implementation; this document does not claim new fields already exist.

Preserve message-local source numbering, request correlation, sources-to-answer
association, completed-answer reconciliation, and explicit stream completion.
Cancellation or interruption must not persist partial answers. Refresh restores
saved evidence rather than rerunning retrieval with the current configuration.

## Acceptance

Verify TXT and Markdown uploads, long heading paths, code/table excerpts, multiple
children for one parent, citation selection across messages, historical snapshots,
deletion, refresh, follow-ups, and cancellation. Check desktop, tablet, and mobile
layouts and keyboard navigation. Use deterministic frontend/browser tests plus a
separate real-provider workflow; use the [evaluation plan](v1-evaluation-plan.md)
for answer quality rather than UI assertions alone.
