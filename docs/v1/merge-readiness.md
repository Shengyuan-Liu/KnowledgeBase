# v1 Merge Readiness — 2026-09-25

**Engineering implementation is ready for user acceptance. No merge is authorized
or performed. Semantic quality validation remains pending independent human review.**
A functional local single-user release must be distinguished from a demonstrated
general answer-quality improvement, as required by the existing release plan.

## Completed evidence

- Markdown/TXT ingestion, structural parent-child storage, hybrid retrieval,
  optional local reranking, bounded evidence packing, source locations, restored
  diagnostics and file-deletion history have implementation and workflow checks.
- Current backend: 554 passed, 1 intentionally skipped live-provider test.
  Frontend: 40 passed. TypeScript/build passed. Browser workflows: 10 passed.
  [Records](../../evals/check-runs/20260925-retrieval-coverage/README.md) retain every
  failed attempt and correction, including Stop causing an unintended extra
  request when its DOM button was reused as Send. Distinct button identities fix
  that regression; the browser test asserts no extra request after cancellation.
- The [previous real-provider UI workflow](../../evals/browser-runs/20260925-semantic-ui-1/README.md)
  covers source inspection, follow-up, refresh and deletion. It predates this
  parent-scoring option; the new option has API/SSE/restart/deletion tests and a
  scoped real-provider answer probe, not a new full real-provider UI run.
- [Parent scoring comparison](../../evals/library-runs/20260925-parent-reranking/README.md):
  both known semantic coverage misses recover only with parent scoring plus the
  separately increased 6144-token budget. No new annotated-span regressions on
  the 21 answerable development questions. Input usage and local compute increase.
  This does not justify changing defaults.
- [Generation judgment supplement](../../evals/library-runs/20260925-review-supplement-3/README.md):
  23/24 valid v11 reviews. One remaining review fails because a filename claim is
  supported by metadata but has no source-text line IDs; preserve the invalid
  outputs rather than repairing them or presenting a full-set score.

## Recommended merge scope and configuration

Keep structural `parent_child` ingestion, hybrid retrieval, child scoring and the
4096-token evidence budget as checked-in defaults. Shared settings still disable
local reranking unless explicitly enabled. The tested reranking control enables
it explicitly; its quality numbers must not be assigned to the disabled setting.
Semantic ingestion and parent scoring remain opt-in experimental features.
No local `.env` or existing index has been changed by this work.

Do not add query decomposition, another framework or additional product scope to
finish v1. The remaining decision is acceptance of this functional scope and its
recorded limitations, not an automatic promotion of the experimental settings.

## Outstanding release validation

The [existing release gates](v1-evaluation-plan.md#review-and-release-gates) require
criteria frozen before opening a new held-out set and independent human review.
The current 24 questions have been used during development; they cannot be
relabeled held-out. No independent human semantic review is available yet.
Report that gate as pending. The two-question Codex review is development evidence
and cannot satisfy it.

Known answer risks remain: list items sometimes lack local citations; a prior
CPT answer strengthened a qualification; an API-setup expected-point rubric asks
for a constructor the question did not explicitly request. The frozen judge has
known assessment disagreements and the unresolved filename-evidence validation.
Preserve these distinctions: a malformed judge result is not necessarily an
incorrect product answer, and complete retrieved evidence is not proof of a
supported final answer.

The next acceptance step is a small, newly frozen answer set with predefined
coverage, support, latency and token-budget criteria, followed by independent
human inspection of the actual answers and supplied sources. Do not rerun the
familiar benchmark repeatedly or tune on that new set while calling it held-out.
The user decides whether to accept a functional release with semantic validation
explicitly pending, or complete that review before approving the v1 merge.
