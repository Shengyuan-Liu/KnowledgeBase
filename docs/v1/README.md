# KnowledgeBase v1

**The user-approved implementation is merged locally into `main` at `483a156`.**
Default functional acceptance and the final real-provider browser workflow pass.
Start with the [v1 release summary](release-summary.md) for everything delivered,
default settings, experiment status, evidence and the distinction between functional
completion and independent quality validation.

## Delivered functionality

- Source-preserving TXT/Markdown parsing, structural sentence chunking and storage.
- Parent-child indexing, hybrid BM25/vector retrieval and RRF fusion.
- Budgeted parent/child context with source identity and recorded exclusions.
- Explicit document scope and representative selection for multi-file questions.
- Grounding prompts, claim-local citations and document-by-document comparisons.
- Markdown upload, original source locations and retrieval diagnostics in the UI,
  including restored history and deleted-source evidence.
- Optional local BGE reranking and experimental semantic/parent-scoring strategies.
- Frozen evaluation records, claim/point review, metric inventory and failure diagnosis.

The default is structural parent-child plus hybrid retrieval, 4096-token evidence,
GPT-4.1 with omitted reasoning effort, and no reranking. Semantic chunking and
parent scoring remain experiments; merged code does not imply default promotion
or a proven general quality gain. See [configuration](../configuration.md).

## Acceptance and remaining limits

- [Merge acceptance](merge-readiness.md): authorization, merge state and limitations.
- [Default service acceptance](../../evals/library-runs/20260926-comparison-awake/README.md):
  11/11 frozen requests/reviews; 26 supported factual claim units; complete annotated
  evidence in seven answerable cases. Bounded development evidence, not held-out accuracy.
- [Final browser acceptance](../../evals/browser-runs/20260926-v1-final-ui-1/README.md):
  real TXT/Markdown uploads, three questions including scoped follow-up and comparison,
  source inspection, refresh, cancellation, deletion and preserved historical evidence.
- [Closeout checks](../../evals/check-runs/20260926-v1-closeout/README.md): build,
  review and documentation verification.
- [Known issues](known-issues.md): unresolved nonfatal stream finalizer warning,
  wording/scope bounds, experimental regressions and independent-validation gap.

No additional feature is required to close the accepted default functional scope.
Independent frozen release-population evaluation and human review are still open;
Codex review and development samples do not fulfill that requirement. Prior failed
attempts and disputed/invalid judge assessments remain intact. Follow the
[measurement policy](../../evals/measurement-policy.md); do not run paid evaluations
after every intermediate edit.

## Design references

1. [Product design](v1-product-design.md): goals, scope and acceptance scenarios.
2. [Technical plan](v1-technical-plan.md): component responsibilities and stage status.
3. [Frontend design](v1-frontend-design.md): uploads, evidence navigation and diagnostics.
4. [System design](v1-system-design.md): ingestion and question-answering architecture.
5. [Evaluation plan](v1-evaluation-plan.md): controlled comparisons and independent quality requirements.

## Version boundary and workflow

The application remains local, single-user and English-only. Existing MVP file
management, streaming, follow-up and conversation restoration are retained and
extended. See the [MVP release report](../../evals/analyses/2026-09-21-mvp-release.md).
PDF/OCR, agents, multi-user accounts and hosted deployment are outside v1.

Markdown ingestion merged at `282158a`; parent-child and hybrid retrieval at
`cd10620`; remaining accepted v1 work at `483a156`. The user also explicitly
authorized merging closeout documentation and final UI evidence (`360a982` and
`55837b0`) on 2026-09-26. Continue subsequent v1 work on `v1`, following
[AGENTS.md](../../AGENTS.md); each future merge needs separate user authorization.
