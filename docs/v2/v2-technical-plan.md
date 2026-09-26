# KnowledgeBase v2 Technical Plan

Status: proposed implementation guidance, not an implemented API or schema.
Use the current [project structure](../project-structure.md) and accepted
[v1 behavior](../v1/release-summary.md) as the baseline.

## Architecture and Ownership

Retain FastAPI, ordinary Python services, SQLite, Chroma, and the React workspace.
Share the controller across API, CLI, and evaluation entry points. No workflow
framework, graph database, distributed queue, or agent framework is required.

| Proposed location | Responsibilities and function guidance |
| --- | --- |
| `rag/pdf.py` (new) | Convert PDF bytes into extracted text, ordered blocks, page provenance, and extraction limitations; no database or retrieval work |
| `rag/planning.py` (new) | Produce bounded question requirements and independent/dependent queries; retain evidence references for derived search targets |
| `rag/sufficiency.py` (new) | Assess required points against supplied excerpts and return supported/partial/missing/conflicting decisions with evidence references |
| `rag/retrieval.py`, `rag/packing.py` | Expose bounded candidate retrieval for reuse across queries; merge candidates and pack one final context |
| `services/chat.py` | Own controller state, scope, limits, cancellation, generation, and atomic completed-turn persistence |
| `services/files.py`, `storage/*` | Own PDF asset lifecycle, parsed provenance, index writes, snapshots, and deletion |
| `schemas.py`, `config.py` | Define typed application records and explicit settings passed by entry points |
| `api/files.py`, `api/streaming.py` | Serve original assets by file identity and expose progress without moving business logic into routes |
| `frontend/src/` | Add PDF evidence navigation and retrieval progress to the existing workspace |

These are responsibility boundaries, not a requirement for one file per helper.
The user writes Python by default. Before each implementation stage, explain the
chosen functions, their inputs/outputs, and the invariants they preserve; follow
[AGENTS.md](../../AGENTS.md) for any explicit implementation authorization.

## PDF Source Contract

Keep original PDF bytes as a local asset under the configured data directory,
addressed by generated file identity rather than an arbitrary caller path. Record
the original content hash separately from the extraction hash. Select one parser
after checking representative PDFs; do not add a speculative parser fallback chain.

The parser produces an immutable extraction revision containing:

- Canonical extracted text and ordered structural blocks.
- Page count, physical page indices, optional printed labels, and page dimensions.
- A mapping from extracted character spans to page regions. Record bounding boxes
  and their coordinate system when available; preserve multiple regions for a
  span crossing pages or columns. A block-level box must not imply word precision.
- Table identity and structural associations, including headers and notes when
  extracted. Serialization syntax remains distinguishable from source content.
- Parser/version/model settings, extraction hash, and known omissions or warnings.

Use zero-based page indices internally and one-based physical page numbers in
the UI. Store end-exclusive character offsets into the extracted canonical text,
not PDF byte offsets. Every evidence excerpt must equal its stored text slice.
This invariant proves extraction consistency, not original-page fidelity.

Avoid using page boundaries as the only chunking rule. Reuse bounded structural
parents and children, allowing passages to cross pages while retaining all their
locations. Keep table headers and relevant rows together where they fit; if an
oversized table is split, retain its table identity and separately located header
evidence. Count any supplied header/context text in the evidence budget and do
not pretend repeated synthetic headers are literal contiguous source slices.

## Ingestion and Existing Data

Dispatch by supported format before the existing UTF-8 text decoder. PDF bytes
must not pass through TXT decoding. Retain the Processing, Ready, and Failed
lifecycle; a Ready PDF means its supported extracted content was indexed, not
that every visual element was understood. Surface extraction limitations.

Store original asset, extraction, parents/children, and vectors before completing
the Ready transition. Extend existing failed/interrupted-upload cleanup to PDF
assets and metadata; account for filesystem, SQLite, and Chroma not sharing one
transaction. Use the existing recovery approach rather than introducing a job
system solely for this plan. Measure local parser resource and blocking behavior
before deciding whether ingestion needs a separate worker.

Deletion first makes a file ineligible, then removes vectors, source records, and
original asset with retryable cleanup under the existing lifecycle. Future rounds
must recheck eligibility. Completed snapshots retain excerpts, locations, and
extraction identity; original-page viewing depends on the live asset.

Use isolated data directories during development. Version additive provenance
and trace records so old TXT/Markdown snapshots remain readable without fabricated
PDF locations. Finalize the migration with the selected schema. Changes to parser,
chunk boundaries, embedding, or indexed text require affected files to be reindexed
from originals; never silently replace the user's existing library. History keeps
the original saved extraction identity after a reindex.

## Retrieval Controller

1. Preserve the original question; reuse follow-up resolution and resolve file
   scope. Treat recent history as reference context, not new factual evidence.
2. Produce a compact plan: required answer points, a direct or decomposed route,
   initial queries, and any dependent requirements. Keep model-produced records
   typed; normal schema validation does not justify a response-repair loop.
3. Execute the allowed queries through the existing Ready-only BM25/vector path,
   preserving route scores and RRF ranks. Existing optional reranking stays an
   explicitly configured component, disabled in the initial baseline.
4. Merge query candidate lists by stable child ID. The proposed starting merge
   uses equal-weight RRF over each query's fused list with deterministic ID ties;
   preserve these ranks separately from within-query lexical/vector fusion.
   Repeated identical queries must not create extra ranking votes.
5. Select representatives for required points/documents where available, expand
   parents, deduplicate, and pack a single context. Record exclusions and which
   requirements lose support to the budget. Do not concatenate complete contexts
   from every query and thereby multiply the final evidence allowance.
6. Assess the required points against that packed context. A direct query with
   sufficient evidence ends after its first retrieval round. It still incurs the
   enabled plan/check overhead; measure this rather than claiming v1 latency.
7. If an unresolved dependency has an evidence-backed search target, or a missing
   point has a useful supplementary query, execute another bounded round. Derived
   entities/claims retain source references; hypothetical search terms are not facts.
8. Repack and reassess the accumulated eligible evidence. Finish with a frozen
   evidence set, source numbering, and required-point status. Generate once from
   that set and stream the answer. Save only the completed exchange and its trace.

All queries inherit the user's allowed file scope; a subquery can narrow it but
cannot expand it. A multi-hop need outside that scope becomes an explicit missing
point. PDF text and retrieved passages are evidence, not controller instructions.

### Sufficiency and Termination

The assessment returns one status per requirement: `supported`, `partial`,
`missing`, or `conflicting`, with excerpt references and a short observable
gap description. It does not produce a confidence percentage or expose private
model reasoning. Retrieval scores cannot substitute for support assessment.

Intermediate assessments may change when packing changes. The final assessment
must describe the exact final context, including any missing evidence removed by
the budget. The controller never supplies its own intermediate prose as a source.
An optional table header or qualifying excerpt is also evidence and must be saved.

| Proposed starting bound | Semantics |
| --- | --- |
| 3 retrieval rounds | Initial round plus at most two further rounds; a round can contain multiple independent queries |
| 6 query executions total | Includes original, decomposed, and dependent queries; a lexical/vector pair is one query execution |
| 6 required answer points | Larger tasks disclose the limit and request narrowing instead of silently dropping requested dimensions |
| 1 planning call and at most 3 assessments | At most one assessment for each round; follow-up resolution and final generation are counted separately |
| 4096 final evidence tokens | Retain the v1 starting budget, including source labels; intermediate calls also need explicit input/output caps |
| Sequential query execution initially | Easier reproducible accounting; parallelism is a later measured optimization |

These are proposed development settings, not accepted optimal defaults. Implement
them through the existing Settings and `.env.example`, with credentials only in
ignored `.env`. Before enabling live execution, resolve per-call input/output
caps and a request deadline, reserve room for final generation, and record them.
Existing provider retries consume the deadline and must be reported as attempts;
logical call limits alone do not bound time or billed usage.

Stop on supported requirements, exhausted limits, no eligible next query, or a
supplementary round that adds no new canonical evidence. A new chunk ID containing
only previously seen source spans does not count as new evidence. Record a stop
reason. Partial/conflicting evidence yields a qualified answer; no answerable
points yields abstention. Provider/schema errors remain explicit request failures,
not successful abstentions or triggers for unbounded model repair. Cancellation
applies throughout the controller, not just during final generation.

## Records and Interfaces

Extend application snapshots with PDF extraction/page provenance and a versioned
retrieval trace: original/resolved question, scope, requirements, queries and
dependencies, per-round ranks, included/excluded evidence, assessments, limits,
stop reason, timings, and available usage. These are proposed logical records,
not necessarily separate tables. Retain canonical evidence once and reference it
from trace entries where possible.

Keep existing chat endpoints. Add a scoped original-file read endpoint and typed
progress events during implementation; exact route/event schemas must be finalized
with corresponding tests. Stable internal evidence IDs precede message-local
citation numbering. Publish final numbered sources only after the retrieval loop
finishes so citations do not change while the answer streams. Complete JSON,
SSE completion, and history must agree about sources and trace identity.

## Implementation Sequence

| Stage | Deliverable | Verification focus |
| --- | --- | --- |
| 1 | PDF parser adapter and immutable provenance | Visual extraction review; reading order, table associations, page mapping |
| 2 | Asset/storage/ingestion and page viewer | Upload, source slicing, page navigation, deletion, restart, old history |
| 3 | Decomposition and evidence-dependent retrieval | Requirement coverage, scope, candidate merge, budget, dependency references |
| 4 | Sufficiency assessment and finite supplementary loop | Supported/missing/conflicting decisions, no-progress stop, partial answers, cancellation |
| 5 | Integrated UI and release acceptance | Frozen comparisons, saved traces, actual answers/citations, latency and cost |

Use scoped tests during development and retained records under the
[measurement policy](../../evals/measurement-policy.md). Run paid/full evaluation
only at feature acceptance or on explicit request. Commit each completed change;
user acceptance and merge authorization remain separate.

## Primary References

- [Docling document model](https://docling-project.github.io/docling/concepts/docling_document/): structure, reading order, and available layout/provenance metadata; a parser candidate, not a selection or quality guarantee.
- [IRCoT](https://arxiv.org/abs/2212.10509): retrieval interleaved with multi-step reasoning; conceptual background for dependent retrieval.
- [CRAG](https://arxiv.org/abs/2401.15884): retrieval assessment guiding further actions; conceptual background for supplementary retrieval.

This design is not a reproduction of those research systems. In particular, it
does not add CRAG's external web search or import published gains as local results.
