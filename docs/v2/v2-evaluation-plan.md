# KnowledgeBase v2 Evaluation Plan

Status: proposed release protocol, with a first
[live PDF development comparison](../../evals/library-runs/20260927-v2-pdf-live/README.md)
now recorded. It retains a failed baseline and repaired replay; acceptance gates
remain unmet, and the A/D comparison is not a complete B/C ablation or held-out
release evaluation. A scoped
[parser comparison and adapter check](../../evals/check-runs/20260926-pdf-parser-selection/README.md)
is also recorded. Follow the complete
[measurement policy](../../evals/measurement-policy.md).

## Populations and Ground Truth

Freeze original PDF bytes before writing questions. Record content hashes, source
rights/provenance, extraction versions, and reference annotations. Start with
digital prose, two-column pages, tables with notes/units, and cross-page passages.
Include explicit unsupported-content examples to verify limitation reporting.
OCR, visual chart/figure understanding, and formula understanding are deferred
from v2. Evaluate their limitation reporting, not recognition quality; separate
quality populations belong to a later feature that explicitly adds those abilities.

Annotate facts and locations against the original rendered pages, not exclusively
against parser output: an omitted passage must remain a detectable extraction
failure. Use physical page indices, regions, expected text/table associations, and
fact IDs stable across parsers. For retrieval comparisons using one extraction,
also retain canonical character spans. Never compare chunk-ID recall across
different boundaries as though the labeled units were identical.

Question groups must include simple facts, paraphrases, exact names, table values
with qualifiers, compound comparisons, evidence-dependent questions, follow-ups,
restricted file scope, conflicts, partially answerable questions, and fully
unanswerable questions. Annotate intermediate dependency evidence as well as the
final answer facts. Retain complete conversation sequences for follow-ups.

Use development questions for parser/controller tuning. Freeze separate held-out
questions, corpus/reference population, rubric, and release thresholds before
opening final results. A new question on already tuned material is not sufficient
evidence of independent release validation. Existing v1 development results are
historical context, not v2 scores or an independent held-out baseline.

## Comparisons

| Comparison | Hold fixed | Interpretation |
| --- | --- | --- |
| PDF extraction candidates | Original files, original-page annotations, device/resource conditions | Reading order, table fidelity, page mapping, omissions, ingestion cost |
| A: Single-pass retrieval | Selected PDF extraction/index, v1 hybrid/packing settings, answer model/prompt | Baseline using v1 retrieval behavior on the new PDF corpus; not a claim that v1 already uploads PDFs |
| B: Decomposition | A plus bounded independent query planning | Coverage benefit and overhead from decomposed searches |
| C: Dependent retrieval | B plus evidence-backed next queries; no gap-driven supplementary search | Contribution of resolving dependent information needs |
| D: Sufficiency-driven retrieval | C plus gap assessments and bounded supplementary queries | End-to-end effect of adaptive missing-evidence search |

Use the same final answer prompt across A-D so prompt changes do not masquerade
as retrieval gains. All arms save their actual evidence, outputs, settings, and
termination behavior. D's added checking overhead is part of its total cost.
Keep parser, chunks, embedding, optional reranker setting, final context budget,
and question population fixed across A-D. Report used query/call counts: D having
more retrieval compute is a tradeoff, not an equal-compute superiority claim.

For a sufficiency routing ablation, assess C's frozen context without acting on
the result and compare with D using the same assessor. This separates assessment
quality from the benefit of its follow-up actions. Run such comparisons when the
complete feature is ready; do not launch every arm after intermediate edits.

## Complete Metric Inventory

For every executed check, record each policy metric as `measured`,
`not_applicable`, or `unavailable` with its reason, unit, sample count, definition,
aggregation, and artifact location. Missing values are never zero.

| Metric | v2 measurement requirements |
| --- | --- |
| Recall@K | Stable relevant facts/spans covered at each query route, fusion stage, round union, and final selection; disclose label completeness |
| Precision@K | Define candidate relevance from frozen source annotations; disclose fewer-than-K handling and incomplete labels |
| Hit Rate@K | Eligible questions with a relevant candidate; report simple and dependent question groups separately |
| MRR | First relevant result under an explicitly named ordering and cutoff; misses contribute zero |
| NDCG@K | Freeze graded relevance, gain/discount, and ideal ranking; do not mix child and fact evaluation units |
| Final evidence coverage | Required facts/spans in actual final packed context; report partial/full support and intermediate dependency coverage |
| Answer correctness | Agreement with original-page reference facts under the frozen rubric |
| Faithfulness | Claim-level support in supplied context, separate from original-page extraction correctness |
| Answer completeness | Required points actually answered, including both documents and comparison dimensions |
| Answer relevance | Response focus under a fixed rubric; a large retrieved context is not a relevant answer |
| Citation support | Cited excerpt supports its associated claim; check original-page fidelity separately |
| Citation coverage | Required factual claims with supporting citations; define claim-free answer handling |
| Abstention | Appropriate abstention on unanswerable cases and incorrect abstention on answerable cases with separate denominators; track partial-answer gaps separately |
| First-answer-delta latency | Request start to first nonempty final answer delta; progress events do not qualify |
| Complete-response latency | Request start to completed response under a stated API/UI boundary |
| Stage latency | Parsing, planning/resolution, per-query embedding/search/fusion/reranking, packing, each assessment, and generation |
| Token usage and cost | Available actual usage for resolution, planning, embeddings, assessment, and generation; evidence tokens and local compute separately; billed cost unavailable unless exposed |
| Reliability | Success/error/timeout/retry counts and rates for requests and attempts, including failed plans/checks and cancellations |
| Concurrency and throughput | Actual request concurrency and completed requests per observed interval; sequential results do not establish load capacity |
| Ingestion and index | Upload-to-searchable time, original asset/extraction/vector storage size, restart, reindex/update, and deletion behavior |

Record K explicitly. A proposed starting report uses candidate K=5 and K=20,
and separately reports the configured final selection. In multi-query runs,
per-query metrics are diagnostic; the original user question remains the primary
evaluation unit. Freeze round-union ordering using the recorded merge algorithm.
Union overlapping source spans and deduplicate facts before coverage aggregation.
Do not score unanswerable questions with no gold evidence as zero recall.

## PDF and Controller-specific Checks

| Area | Additional observations |
| --- | --- |
| Extraction | Missing/spurious text, reading-order errors, table header/value/unit/note association, page mapping, printed-label handling |
| Dependencies | Whether required intermediate facts were retrieved and each derived target is tied to supporting evidence |
| Sufficiency assessment | Supported/partial/missing/conflicting decisions against reviewed labels; false sufficiency and false insufficiency rates with explicit denominators |
| Supplementary search | Trigger count, additional supported points, unnecessary searches on already sufficient cases, no-progress stops, and budget exhaustion |
| Scope and lifecycle | Every round stays eligible/in-scope; cancellation stops work; deletion removes live assets while preserving saved evidence |

An assessment can be structurally valid and semantically wrong. Preserve both
kinds of failure. Review representative false-sufficiency cases, incorrect
abstentions, unsupported derived queries, and extraction-induced wrong answers.
Keep source extraction errors distinct from retrieval misses, packing losses,
assessment errors, and generation errors.

## Records and Review

Retain commands, base commit plus changed-file hashes, corpus/annotation hashes,
device, concurrency, settings, resolved models/revisions, prompt versions, warmup,
queue/model-loading inclusion, deadlines/retries, and actual usage when available.
Save original/resolved questions, requirements, dependency references, every
query's candidates/ranks, each packed context and assessment, exclusions, stop
reason, final answer, and claim/point review. Do not request or store private model
reasoning; structured decisions and evidence references provide the audit trail.

For timing distributions, report sample count, mean, P50, P95, percentile method,
and treatment of failures. Separate cold parser/model loading and repeated warm
runs. Report quality and performance independently, with per-question improvements
and regressions as well as aggregates. Save runs append-only, including failures.

Offline tests verify contracts with controlled providers; their durations are not
production performance, and live answer quality/cost are not applicable. Visual
PDF review must inspect original pages and extraction side by side. Record whether
the reviewer is Codex, another model, or a human; never label model review human.

## Acceptance Gates

1. Pass relevant scoped tests for PDF provenance, asset cleanup, chunk/page mapping,
   controller limits/scope, dependencies, context packing, Stop, and old snapshots.
2. Verify the integrated browser flow with PDF upload, page navigation, simple and
   dependent questions, missing evidence, refresh, deletion, and TXT/MD regression.
3. Review actual final answers and original-page evidence on the frozen functional
   set. Structural trace validity and citation membership alone cannot pass quality.
4. Publish A-D comparisons with parser configuration, regressions, latency/cost,
   and missing telemetry. Select settings from development evidence and freeze
   quality/performance thresholds before opening held-out results.
5. Obtain independent human review before claiming independently validated broad
   quality. If unavailable, report that gap; Codex can still provide a clearly
   labeled functional acceptance recommendation when the user requests it.
6. Let the user decide feature acceptance and authorize each merge explicitly.

No runtime checks or paid evaluation are required for this documentation change.
Its own content/link/format review is retained in the
[design review record](../../evals/check-runs/20260926T195804Z-v2-design/README.md).
