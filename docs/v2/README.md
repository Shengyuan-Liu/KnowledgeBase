# KnowledgeBase v2

Status: functional implementation, scoped acceptance and documentation completed
on `v2` on 2026-10-01. User acceptance and an explicit merge into `main` remain
pending. See the [release summary](release-summary.md) for usage, evidence and limits.

## Delivered scope

1. Digital PDF ingestion, supported table structures and physical page citations.
2. Independent question decomposition and evidence-dependent retrieval.
3. Evidence sufficiency assessment and bounded supplementary retrieval.

Use **Plan complex questions** to enable the complete controller. Single-pass
retrieval remains the default. OCR, visual figures/charts, mathematical formula
understanding, hosted multi-user deployment and new external connectors are deferred.

## Closeout evidence

The [final report](../../evals/library-runs/20261001-v2-release/README.md) records
6/6 matched real-PDF cases, one actual two-round synthetic dependency chain,
5/5 new-to-project held-out cases, and a four-case A-D comparison. Backend tests
pass 851 with one explicitly opt-in live smoke skipped; frontend tests pass 49,
and controlled browser regressions pass 21. Real source navigation and lifecycle
checks also pass. All failed attempts and missing measurements remain visible.

This is a functional acceptance recommendation by Codex, not independent human
validation or a broad accuracy guarantee. In particular, control-arm failures and
unproven supplementary-search quality benefit remain in the report.

## Documentation

- [Release summary and known limits](release-summary.md)
- [Product design](v2-product-design.md)
- [Technical plan](v2-technical-plan.md)
- [System design](v2-system-design.md)
- [Frontend design](v2-frontend-design.md)
- [Evaluation protocol](v2-evaluation-plan.md)
- [Historical development and retained failures](development-history.md)
- [PDF setup and integration](../pdf-integration.md)
- [Independent planning](../planned-retrieval.md)
- [Dependent retrieval](../dependent-retrieval.md)
- [Evidence sufficiency](../evidence-sufficiency.md)

Scope is frozen for this closeout. Further improvements and newly reported issues
are subsequent work; the user retains the decision to accept and merge v2.
