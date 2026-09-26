# KnowledgeBase v1 Product Design

## Product Goal

Help a single user ask questions over TXT and Markdown materials by retrieving
more relevant evidence and supplying enough surrounding context to interpret it.
v1 improves the existing personal knowledge base; it does not add a separate
agent product or change the local deployment model.

Status: the scoped implementation was accepted and merged locally at `483a156`
on 2026-09-26. This document retains the product goals and acceptance scenarios.
See the [release summary](release-summary.md) for delivered defaults, opt-in
experiments and evidence. The [evaluation plan](v1-evaluation-plan.md) still
distinguishes functional acceptance from pending independent quality validation.

## Motivation

The [MVP release inspection](../../evals/analyses/2026-09-21-mvp-release.md) found
missed evidence about GPA, online study, and CPT, as well as unsupported additions
and a fabricated quotation. These are observations from saved development runs,
not newly reproduced results. The inspection does not establish that chunk
boundaries caused every retrieval miss.

v1 targets evidence retrieval and context organization. Better retrieval alone
does not establish correct answers: answer support and quotation fidelity remain
separate evaluation requirements.

## Scope

| Capability | Intended user benefit | Boundary |
| --- | --- | --- |
| UTF-8 `.txt` and `.md` uploads | Use plain notes and structured Markdown documents | No PDF, OCR, images, or automatic link fetching |
| Structure-aware and sentence-aware chunking | Keep headings, paragraphs, words, and sentences meaningful where size limits allow | Define explicit handling for oversized units; do not promise every sentence always fits |
| Parent-child chunks | Find a focused passage and provide its broader local context | A parent is a bounded source region, not automatically the entire document |
| BM25 plus vector retrieval | Combine lexical matching with semantic matching | Both routes search eligible child chunks |
| RRF fusion | Produce one candidate ranking from both retrieval routes | Fusion uses ranks, not directly added raw scores |
| Reranking | Prioritize relevant candidates before context expansion | Cannot recover evidence absent from the candidate set |
| Embedding-based semantic chunking | Test whether grouping related sentences improves retrieval | Included as a selectable experiment; default adoption requires evidence |

## User Workflow

1. Upload TXT or Markdown and wait for Ready.
2. Ask a question or continue a conversation. No retrieval settings are required in the chat composer.
3. Receive a streamed answer with numbered sources.
4. Open a citation to inspect the exact supplied parent excerpt, its file, and its heading path when available.
5. Optionally open diagnostics to see which child passages led to that evidence.

File deletion excludes its content from both retrieval routes and future parent
expansion. Completed conversations retain their original evidence snapshots.
Conversation history resolves references; it is not factual evidence for new answers.

## Chunking Decisions

The default strategy respects document structure and sentence boundaries before
resorting to smaller units under a size limit. Markdown headings define useful
section boundaries; list items and fenced code blocks retain their structure
where they fit. TXT uses paragraphs and sentences without inventing headings.

Semantic chunking makes a different decision: it uses sentence embeddings to
identify topic changes. It must be compared against the simpler structural
strategy. Both strategies use the same parent-child evidence contract.

## Acceptance Scenarios

| Scenario | Required behavior |
| --- | --- |
| Upload a Markdown course note | It becomes searchable; heading paths and exact source locations remain available |
| Search for a course code or abbreviation | The lexical route can contribute the annotated matching child passage |
| Ask a paraphrased question | The vector route can contribute relevant evidence without identical wording |
| A requirement and its exception occur in adjacent sentences | The selected parent includes both when they belong to that parent; answer inspection checks the qualification |
| Several selected children share one parent | The parent is supplied once and keeps all selected child associations |
| Inspect a numbered source | Display the exact evidence supplied for that source, rather than only the small matching child |
| A sentence exceeds a configured chunk limit | Apply the documented splitting policy and preserve source locations |
| Ask about different years or conflicting rules | Preserve source context and make conflicts explicit |
| Ask for information absent from retrieved evidence | State the evidence limit; do not infer that the entire document lacks the information |
| Delete a file, then ask a follow-up | Neither BM25 nor vector search supplies it; historical excerpts remain inspectable |

Fixtures make these behaviors testable; passing them is not a general accuracy guarantee.
Version acceptance also requires the [evaluation and release checks](v1-evaluation-plan.md).

## Outside v1

PDF/OCR, web ingestion, remote Markdown resources, knowledge graphs, autonomous
question decomposition, long-term user memory, multi-user access, hosted deployment,
and a new document-organization interface are outside this version. No new
framework, vector database, or model provider is required solely by this scope.
