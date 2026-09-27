# KnowledgeBase v2

Status: designs prepared on 2026-09-26; the stage 1 [PDF adapter](../pdf-parsing.md)
and stage 2 [PDF integration](../pdf-integration.md) are implemented with recorded
checks and unresolved parser fidelity limits. Stage 3b [automatic independent
planning](../planned-retrieval.md) now connects the stage 3a executor to JSON/SSE
chat, CLI, progress display and saved history with bounded requests. It is opt-in
and offline-tested. Stage 3c [dependent retrieval](../dependent-retrieval.md) now
binds follow-up targets to retained source quotes across at most three rounds.
Stage 4 [sufficiency control](../evidence-sufficiency.md) now assesses packed
evidence and runs bounded gap searches through the same opt-in mode. The first
[live PDF development comparison](../../evals/library-runs/20260927-v2-pdf-live/README.md)
is recorded, including targeted repairs and a frozen replay. Acceptance gates
still fail; no feature acceptance or merge is implied.
The [financial packing repair](../../evals/check-runs/20260927-pdf-evidence-packing/README.md)
now retains selected sales rows with their period headers and nearby units in the
same 4,096-token budget. The subsequent
[passage-selection repair](../../evals/check-runs/20260927-assessment-passages/README.md)
replaces assessor-authored quotes with IDs resolved to exact source text and pages.
The subsequent [financial live replay](../../evals/library-runs/20260927-financial-acceptance/README.md)
completes all six requests with correct requested facts, but a planned income
bullet lacks an inline citation.
The [offline citation/context repair](../../evals/check-runs/20260927-citation-context/README.md)
now links answer requirements to current source numbers, adds a per-item citation
example, and displays exact related table headers separately from assessor-selected
passages. The subsequent [six-request citation replay](../../evals/library-runs/20260927-financial-citation-acceptance/README.md)
passes its scoped gates: all requested facts and all 16 current factual groups
have support under the unchanged rubric, which allows documented fiscal-period
inference. The subsequent
[dense-table repair](../../evals/check-runs/20260927-dense-table/README.md)
recovers the four missing Alabama values, all three annotated state rows, explicit
blanks and grouped headers from native PDF rules/text. Four other frozen document
controls remain unchanged. The technical report's merged-row failure, unannotated
dense-table rows and broader live acceptance remain outstanding. Existing library
entries require a fresh upload to use the revised extraction.

## Confirmed Feature Areas

1. **PDF ingestion and page citations:** ask grounded questions over PDF content
   and navigate from an answer to the corresponding original page.
2. **Query decomposition and multi-hop retrieval:** cover multiple question
   requirements and retrieve further evidence when a later query depends on an
   earlier finding.
3. **Evidence sufficiency assessment and bounded supplementary retrieval:**
   identify missing support, search for it within explicit limits, and answer
   with supported facts and clearly stated remaining gaps.

The core PDF scope is digitally generated English documents, including
representative multi-column pages and tables. The user requested papers, lecture
material and company/technical reports. On 2026-09-26, the user confirmed that OCR, visual chart/figure
understanding, and mathematical formula understanding can be deferred. They are
outside v2; text captions and supported table structures remain in scope.

## Design Set

| Document | Purpose |
| --- | --- |
| [Product design](v2-product-design.md) | User workflows, scope, exclusions, and functional acceptance |
| [Technical plan](v2-technical-plan.md) | Source contracts, bounded retrieval controller, module responsibilities, and implementation stages |
| [Frontend design](v2-frontend-design.md) | PDF navigation, progress, missing-information presentation, and history |
| [System design](v2-system-design.md) | Ingestion, retrieval state flow, storage, and lifecycle boundaries |
| [Evaluation plan](v2-evaluation-plan.md) | Frozen comparisons, PDF fidelity, multi-hop evidence, quality, latency, and cost |

## Baseline and Non-goals

Build on the accepted [v1 release](../v1/release-summary.md): source-preserving
TXT/Markdown ingestion, structural parent-child chunks, BM25/vector RRF,
budgeted evidence, document scope, streaming, and saved evidence. Reranking stays
disabled and semantic chunking stays experimental unless separately evaluated
and accepted. v2 does not rename those existing features as new work.

Retain the local, single-user, English-only product. Hosted deployment, accounts,
web search, remote connectors, GraphRAG, whole-library thematic summaries, and
autonomous external actions are outside this plan. The multi-hop controller is
a bounded local-library workflow, not a requirement for a multi-agent framework.

## Proposed Sequence and Open Decisions

Deliver PDF ingestion/page navigation first, decomposition and multi-hop retrieval
second, and sufficiency-driven supplementary retrieval third. Each stage has its
own scoped checks and an acceptance comparison when ready. The final release
combines all three; stage completion does not establish a general quality gain.

| Decision | Current position | Resolve by |
| --- | --- | --- |
| Representative PDF population | Papers, lecture material, and company/technical reports; five development documents frozen | Confirmed by the user on 2026-09-26 |
| OCR and mixed scanned pages | OCR deferred by the user; disclose content that is not indexed | Confirmed for v2; revisit in a later version |
| Figures and formulas | Text captions may be indexed; visual interpretation and formula reasoning are deferred by the user | Confirmed for v2; revisit in a later version |
| Parser and page viewer | Docling plus scoped native recovery for collapsed ruled tables; known merged-row/order failures remain; bundled PDF.js page viewer | See [PDF parsing](../pdf-parsing.md) |
| Query/checker models and limits | Six-request citation follow-up passes its frozen scoped gates; broader semantic decisions and unnecessary searches remain unverified | Broader acceptance still required |
| Quality, latency, and cost thresholds | Freeze from development evidence before held-out evaluation | Evaluation preparation |
| v2 development branch | Use `v2` for all v2 implementation and documentation commits | Confirmed by the user on 2026-09-26 |

Keep only `main` and the active version branch, currently `v2`, locally and on
GitHub. The retired `v1` branch had no commits outside `main`; its release history
remains available in Git and the v1 documentation.

Follow [AGENTS.md](../../AGENTS.md) for English project text, Python ownership,
verification, and commits. The user subsequently requested implementation of the
PDF adapter and integration stages. User acceptance and explicit feature-specific merge
authorization remain separate from passing checks. No merge is part of this task.

## Documentation Verification

The [design review record](../../evals/check-runs/20260926T195804Z-v2-design/README.md)
records content, links, and formatting checks. It is not a runtime or RAG evaluation.
The subsequent [branch and scope review](../../evals/check-runs/20260926T200634Z-v2-scope/README.md)
records the user-confirmed branch and deferred capabilities without changing the
historical review.
