# KnowledgeBase v1 Design

Status: implementation started; this directory defines the next version after the local MVP.
The standalone [document parser](../document-parsing.md),
[structural chunker](../structural-chunking.md), and
[document storage](../document-storage.md) are implemented with tests.
They are not yet connected to uploads. The remaining v1 pipeline is planned;
these documents do not claim that the full version is implemented or its quality measured.

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
