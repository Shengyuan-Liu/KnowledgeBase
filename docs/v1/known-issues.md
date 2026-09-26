# v1 Known Issues and Validation Gaps

As of 2026-09-26. These limits accompanied the accepted default v1 functionality;
functional completion does not close the items below.

## KB-V1-001: Nonfatal stream finalizer warning

**Status: unresolved; no observed request or persistence failure in the recorded run.**

The [awake-host acceptance log](../../evals/library-runs/20260926-comparison-awake/README.md)
contains `BoundAsyncStream.__aiter__: ValueError: async generator already executing`.
All 11 requests and saved snapshots passed their checks. The
[scoped cleanup checks](../../evals/check-runs/20260926-generation-diagnostics/README.md)
include 25 sequential real-SDK streams over mocked HTTP with forced collection;
the warning did not reproduce. The [final real-provider browser run](../../evals/browser-runs/20260926-v1-final-ui-1/README.md)
also did not show it. Neither observation proves a live-transport fix or absence
of resource leaks.

Follow-up: when it recurs, preserve the complete exception and stream lifecycle,
SDK/runtime versions, cancellation state and request outcome. Obtain a reproducible
live-transport case before a narrow cleanup fix and regression test. Prioritize it
if it affects request completion, persisted answers or resource use. Do not
suppress the warning or edit dependency internals without identifying the cause.

## KB-V1-002: Answer wording and scope limits

**Status: bounded known limitation.**

Some recorded answers repeat conclusions or phrase missing information as a
whole-page absence. The inspected frozen files support those particular claims,
but unseen pages may require excerpt-level qualification. Document recognition
uses bounded syntax; API file IDs disambiguate identities, and there is no new UI
file picker. Follow-up resolution depends on the model. Top-K and evidence budgets
can omit requested files or facts when capacity is insufficient.

See [document scope](../document-scope.md), [grounding](../answer-grounding.md), and
[merge acceptance](merge-readiness.md). The final small-fixture comparison preserves
the page-wide wording limitation; its complete General source supports the absence
claim, but this does not establish general absence detection.

## KB-V1-003: Experimental retrieval regressions

**Status: retained experiments; no default promotion.**

Semantic chunking's [paired run](../../evals/library-runs/20260925T002400Z-semantic-acceptance/README.md)
retains two material evidence regressions. [Parent scoring and packing](../../evals/library-runs/20260925-parent-reranking/README.md)
recover those cases at higher compute/context cost. Structural parent-child remains
the default and reranking remains disabled. A different configuration needs its
own fixed-workload comparison and acceptance, not inherited quality claims.

## KB-V1-004: Independent release quality remains unvalidated

**Status: open validation gap, distinct from implemented functionality.**

The default service and browser checks use bounded development/synthetic questions.
Codex inspected answers, claims, citations and expected points; that is implementer
review, not independent human review. Six newer questions on familiar documents
also do not establish a separate release population. LLM judge validation retains
calibration disagreement and invalid assessments.

To close: freeze an independent corpus/question/reference population and rubric
before selection, retain complete metrics and failures, and obtain independent
human review. Do not tune on the same set and continue to call it held-out. Follow
the [evaluation plan](v1-evaluation-plan.md) and [measurement policy](../../evals/measurement-policy.md).
No further paid sampling was performed to make this closeout look complete.

## Measurement limitations

The [final browser report](../../evals/browser-runs/20260926-v1-final-ui-1/README.md)
records UI completion rather than HTTP completion/first delta. The unchanged API
does not expose actual upstream usage, billing or resolved model revisions. Its
Playwright observer could not read SSE bodies; the original generic error text
mistakenly blamed cancellation for completed responses too. Raw artifacts remain
unchanged, with this correction in the review. The future harness now retains the
actual observer error. This reporting limitation did not prevent checking complete
saved answers, source snapshots or the user workflow; no paid rerun was needed.
