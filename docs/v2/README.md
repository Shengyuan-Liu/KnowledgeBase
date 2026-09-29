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
The subsequent [six-request dense-table live replay](../../evals/library-runs/20260927-dense-table-acceptance/README.md)
does not pass: only 2 of 24 requested point instances are answered correctly.
The recovered table is retrieved but excluded from final evidence by its serialized
context cost. Single-mode state totals are unsupported; planned mode withholds
them. Both grouped/blank-cell requests stop at an incorrectly parsed filename
reference. Evidence packing and quoted-filename scope handling then preceded the
remaining technical-table repair; blank-cell answer behavior was unexercised in that run.
The following [context and scope repair](../../evals/check-runs/20260927-table-context-scope/README.md)
keeps table metadata lossless while reducing its serialized cost, defers table
parent expansion to preserve selected hits, and bounds quoted filename references.
Offline evidence coverage improves from 2/16 to 16/16 on the four frozen requests
with recorded candidates. The [matched live replay](../../evals/library-runs/20260927-table-context-scope-acceptance/README.md)
then supplies all 24 requested evidence points and improves answer correctness from
2/24 to 19/24. All six scopes resolve, but both grouped/blank-cell answers still
confuse column groups or turn printed blanks into zero. Acceptance remains failed;
making table meaning explicit in model context precedes broader table acceptance.

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

## Explicit table cell readings

The [table context regression record](../../evals/check-runs/20260927-table-cell-context/README.md)
documents source-metadata-pdf-v3: row labels, full grouped column paths and explicit
empty-cell markers help distinguish nearby values while preserving canonical
excerpts and page/cell provenance. Twelve frozen offline contexts preserve all
40 requested evidence points within the existing budget. Generated-answer
acceptance is recorded separately in the
[frozen six-request protocol](../../evals/library-runs/20260927-table-cell-context-acceptance/protocol.md).

The [matched live result](../../evals/library-runs/20260927-table-cell-context-acceptance/README.md)
remains below acceptance: five of six requests completed; completed answers scored
19/21 points, with 19/24 intended points delivered. Planned grouped/blank answers
improved to 4/4, but single mode still omits both known blanks and a separate
planned request failed on an unaddressed comparison requirement. This run has one
Codex reviewer and no independent second review; all failures remain recorded.

The [blank-cell and planner regression](../../evals/check-runs/20260927-blank-plan/README.md)
addresses the two remaining failures: explicit blank observations and an auditable,
bounded query for unaddressed decomposed requirements. Its offline checks pass;
the [matched acceptance protocol](../../evals/library-runs/20260927-blank-plan-acceptance/protocol.md)
keeps the same questions, source facts, index and scoring rules.

The [explicit-blank and planner live result](../../evals/library-runs/20260927-blank-plan-acceptance/README.md)
passes the frozen answer gates under single Codex review: 6/6 completions, 24/24
requested points and 21/21 supported, individually cited factual groups. Both modes
now describe the Rentals cells as blank and the state comparison completes. The
coverage-query branch is validated by offline replay; current live plans already
address every requirement. One conditional instruction is still incorrectly marked
missing by the assessor, without affecting the final answer. Independent review,
broader quality and user acceptance remain separate.

The [answer-rule separation regression](../../evals/check-runs/20260927-answer-rules/README.md)
adds an explicit plan field for user answering instructions, keeping them outside
factual evidence requirements. Its 284 scoped tests pass. A controlled replay of
the recorded conditional-instruction failure preserves all four facts and changes
the stop reason to `requirements_supported` when supplied the annotated separated
classification. That offline replay does not establish live model classification
accuracy or general acceptance.

The subsequent [four-case live answer-rule acceptance](../../evals/library-runs/20260928-answer-rules-acceptance/README.md)
completes all cases but fails two gates. The original rule and its paraphrase pass;
a factual conditional question gains an invented answering rule, and a 2016 query
receives unsupported 2015 figures despite explicit source-period headers. Answers
score 11/13 points, with 10/12 factual claim groups supported and individually cited.
This is a fixed-context component run, not a new retrieval or end-to-end acceptance.
Period matching and preservation of the actual user instructions remain open.

The [period/rule constraint update](../../evals/check-runs/20260928-period-rule-constraints/README.md)
rejects newly generated answering rules that do not quote the original question,
and adds explicit period/document/column matching to assessment and generation
instructions. Offline controlled replay verifies rejection and the abstention path
for annotated missing evidence. Wrong-year model output still passes provenance
validation; that offline result did not establish live semantic improvement.

The [matched period/rule live follow-up](../../evals/library-runs/20260928-period-rule-acceptance/README.md)
completes 4/4 cases and improves point delivery from 11/13 to 13/13: unavailable
2016 values are now withheld, and the factual-condition plan no longer invents an
answer rule. Three of four case gates pass. The missing-year plan still adds a
duplicate evidence-availability requirement and incorrectly qualifies Pre-Pawn
Handgun as ungrouped. These planning/wording defects keep acceptance open despite
the correct missing-value answer. No new retrieval or supplementary loop was tested.

The [planner fact-scope regression](../../evals/check-runs/20260928-planner-fact-scope/README.md)
tightens planner instructions around duplicate evidence checks and local column
modifiers, with matching generation guidance for unavailable values. Offline
controls preserve explicit document-explanation questions and verify that an
annotated two-fact missing plan uses the local insufficient-evidence response.
No deterministic semantic filter or live measurement is added by that offline update.

The [matched fact-scope live acceptance](../../evals/library-runs/20260928-planner-fact-scope-acceptance/README.md)
fails: 3/4 completions, 2/4 case gates and 10/13 intended points delivered. The
missing-year duplicate check disappears and the local refusal is correct, but the
Pre-Pawn qualifier remains wrong. The factual-condition case now emits dependent
queries without required target placeholders and fails validation before answering.
Its semantic quality is unavailable; completed answers alone score 10/10 points.
Logical conditions versus retrieval dependencies and the column qualifier remain
open. No product repair or full-loop acceptance is part of this evaluation.

The [dependency-contract offline update](../../evals/check-runs/20260928-planner-dependency-contract/README.md)
adds target presence to the planner's outgoing schema and explicit conditional
versus dependent retrieval examples. It also illustrates the separate Handgun
and Pre-Pawn column names. Recorded targetless queries fail the new schema
constraint; an annotated independent plan retains all three requested facts.
The qualifier error is still a semantic model error, without a runtime repair.
No paid calls or new acceptance scores were part of that offline change.

The [matched dependency-contract live follow-up](../../evals/library-runs/20260929-planner-dependency-acceptance/README.md)
completes 4/4 requests and delivers 13/13 expected points. The factual condition
now uses three independent searches, and Pre-Pawn Handgun retains its correct
column scope. Three of four case gates pass: the factual-condition plan now
duplicates the factual question into `answer_rules`, despite answering correctly.
That semantic classification regression keeps acceptance open. All ten factual
claim groups are supported and individually cited; no full-loop or held-out
quality result is claimed.

The [offline factual-condition rule update](../../evals/check-runs/20260929-factual-condition-rules/README.md)
adds explicit contrasting classifications and a matching provider field description.
It removes ambiguity around preserving a factual condition: the original question
is already passed unchanged to generation, so it need not be copied into
`answer_rules`. Controlled replay preserves the three facts, queries, downstream
requests and existing period/column behavior. The raw semantic error remains
accepted and no paid inference was run in that offline update.

The [matched v8 live follow-up](../../evals/library-runs/20260929-factual-condition-acceptance/README.md)
now passes 4/4 scoped case gates and preserves 13/13 expected answer points. The
factual condition has empty answering rules and three independent fact queries;
actual instructions, column paths and missing-year refusal remain correct. All
ten positive factual groups are supported and individually cited. This single
fixed-context development run does not establish held-out or full retrieval-chain
quality. New questions through the complete retrieval chain and user acceptance
remain open; no merge is authorized by this result.

The [new-question full-chain run](../../evals/library-runs/20260929-new-pdf-chain/README.md)
extends verification to six questions on paper, lecture and financial PDFs. All
six real HTTP/SSE requests complete; five case gates pass and 14/16 expected
points are answered correctly. The lecture answer withholds two indexed page-62
count facts because they do not reach the final context, despite supplementary
retrieval. The selected region contains the slide title without its learning
bullets; no context-budget exclusion causes the miss. All 15 emitted factual
claims have supporting evidence/citations, and the missing-date refusal is
correct. The factual cash-flow condition also retains the intended classification.
This is a new-question check on a familiar development corpus, with one partial
refusal still open; it is not full-chain acceptance or a held-out benchmark. The
next repair should address the concrete lecture retrieval miss before a matched
acceptance run. No product change or merge is part of this evaluation.
