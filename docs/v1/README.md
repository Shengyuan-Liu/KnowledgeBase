# KnowledgeBase v1 Design

Status: implementation started; this directory defines the next version after the local MVP.
The [document parser](../document-parsing.md),
[structural chunker](../structural-chunking.md), and
[document storage](../document-storage.md) are connected to TXT/Markdown ingestion
in the API, CLI, and evaluation runner. The frontend accepts both formats. Offline
tests cover upload, chat, restoration, deletion, and failure cleanup. Feature
acceptance and merging to `main` remain the user's decision.
The [targeted live Markdown acceptance](../../evals/browser-runs/20260922T222123209Z-8d828f17/README.md)
also passed with real providers and seven reviewed questions. This is functional
evidence, not a broad accuracy result or a chunking-quality comparison.
The standalone [parent-child chunker](../parent-child-chunking.md) also produces
bounded parents and children with tested source containment.
[Parent-child storage](../parent-child-storage.md) preserves their relationships
with transactional cleanup and old-data compatibility.
[Parent-child retrieval](../parent-child-retrieval.md) now integrates uploads,
child-only indexing, parent expansion/deduplication, evidence budgets, and saved
diagnostics across API, CLI, and evaluation. It is the default strategy at the user's request and covered by offline
workflow tests. Real-library comparisons are recorded separately; choosing a
default does not establish a general quality improvement.
[Hybrid retrieval](../hybrid-retrieval.md) combines [BM25](../bm25.md) and vector
candidates through [RRF](../rrf.md) across the shared service path. Markdown
ingestion was merged into `main` at `282158a`; parent-child and hybrid retrieval
were merged at `cd10620`.

The `v1` branch also implements optional [local BGE reranking](../reranking.md),
parent-then-child evidence packing, budgeted source identity, and
[automatic evaluation](../../evals/metrics.md). These changes have recorded checks
and development comparisons, but user acceptance and merge approval remain
outstanding. Reranking remains disabled by default in shared settings.

## Remaining Work

1. Accept the opt-in [semantic child-chunking strategy](../semantic-chunking.md),
   now implemented inside unchanged parent regions. Structural parent-child
   chunking remains the default and control. The
   [paired live comparison](../../evals/library-runs/20260925T002400Z-semantic-acceptance/README.md)
   records two substantive evidence regressions; semantic chunking remains experimental.
2. Accept the completed frontend source locations and recorded retrieval
   diagnostics, verified with [offline checks](../../evals/check-runs/20260924-evidence-ui/README.md)
   and a [real-provider browser workflow](../../evals/browser-runs/20260925-semantic-ui-1/README.md).
3. Address observed citation placement and multi-part evidence omissions before
   claiming release quality. Six newly frozen questions on familiar documents
   supplement the development set; an independent release population and human
   review remain outstanding. Do not rerun paid evaluation after intermediate edits.

The current judge protocol is frozen at `claim-inventory-v11`. Its
[review](../../evals/check-runs/20260924-judge-abstention/REVIEW.md) retains one
calibration label mismatch and disputed judgments. Valid judgments are not proof
of answer correctness. Development results are not held-out release accuracy.
Run full evaluation only at feature acceptance or on explicit request, following
the [measurement policy](../../evals/measurement-policy.md).

v1 adds Markdown support, structure-aware and sentence-aware chunking, parent-child
retrieval, BM25/vector hybrid search, RRF fusion, and reranking. Embedding-based
semantic chunking is included as an experimental strategy; evaluation determines
whether it becomes the default.

## Documents

1. [Product design](v1-product-design.md): goals, scope, user behavior, and acceptance scenarios.
2. [Technical plan](v1-technical-plan.md): responsibilities, indexing, retrieval, evidence, and delivery sequence.
3. [Frontend design](v1-frontend-design.md): Markdown uploads, evidence navigation, and retrieval diagnostics.
4. [System design](v1-system-design.md): planned ingestion and question-answering diagrams.
5. [Evaluation plan](v1-evaluation-plan.md): baselines, controlled comparisons, metrics, and release evidence.

## Version Boundary

The [MVP release report](../../evals/analyses/2026-09-21-mvp-release.md) records the
existing baseline and its limitations. The [MVP designs](../mvp/mvp-product-design.md)
remain historical context. This v1 plan supersedes their proposed V2/V3/V4 ordering;
PDF and agent capabilities are not included in v1.

The application remains local, single-user, and English-only. Existing upload,
streaming, follow-up, source inspection, and conversation restoration workflows
remain part of acceptance. Python implementation follows the ownership rules in
[AGENTS.md](../../AGENTS.md).
