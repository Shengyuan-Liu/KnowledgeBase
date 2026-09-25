# v1 Merge Readiness — 2026-09-25

**Do not claim full acceptance yet.** Current default GPT-4.1 passes **4/5**
targeted cases in the [latest correction](../../evals/library-runs/20260925-answer-focus/README.md).
The remaining issue is document scope: an answer requested from the general FAQ
includes an admissions-only fact without identifying that other document. The
fact is supported in context; this is not fabrication or an invalid citation ID.
The question-aligned rubric was frozen before this pass and applied to the same
historical baseline (3/5); original scores remain intact. All five new outputs are
English, but this does not establish general language reliability. No model
default, local `.env` or merge changed.

## Completed engineering evidence

- Markdown/TXT ingestion, structural parent-child storage, hybrid retrieval,
  optional local reranking, bounded evidence packing, source locations, restored
  diagnostics and file-deletion history have implementation/workflow checks.
- Current full backend: **561 passed, 1 intentionally skipped live-provider test**.
  [Records](../../evals/check-runs/20260925-answer-focus/README.md) include
  earlier failures and corrections. Shared generation instructions now explicitly
  bind claims to named sources and table statuses and follow the evidence message.
  The optional answer reasoning setting reaches complete/streaming providers,
  API, CLI and evaluations; blank preserves omitted-parameter behavior.
- Previous frontend: 40 passed; browser workflows: 10 passed; TypeScript/build
  passed. No frontend edits in this correction session.
  [Records](../../evals/check-runs/20260925-retrieval-coverage/README.md) retain the
  Stop/Send button regression and its verified correction.
- The [real-provider UI workflow](../../evals/browser-runs/20260925-semantic-ui-1/README.md)
  covers source inspection, follow-up, refresh and deletion. It predates these
  generation changes; current backend contract tests are fresh, not a new live UI run.

## Functional scope and configuration

Keep structural `parent_child`, hybrid retrieval, child scoring and 4096-token
packing as checked-in defaults. Shared settings disable local reranking unless
enabled. Semantic ingestion and parent scoring remain opt-in experimental options.
[Parent scoring](../../evals/library-runs/20260925-parent-reranking/README.md) recovers
two known semantic coverage misses only with the separately increased 6144-token
budget, with more model input and local compute. It does not justify new defaults.

Default answer model remains GPT-4.1. `ANSWER_REASONING_EFFORT` is blank/omitted.
The five-case GPT-5.4-mini comparisons are candidate observations, not the current
local app's configuration or a newly accepted default. No index re-creation or
embedding change is part of this work.

## Remaining acceptance issues

The original [eight-case service run](../../evals/library-runs/20260925-v1-codex-acceptance/README.md)
remains 7/8: all service/evidence/operational checks passed, but one answer expanded
a table status into an unsupported all-endpoint guarantee. The first
[scope-only correction](../../evals/library-runs/20260925-source-scope/README.md)
remains 3/5. All failures are preserved; none is overwritten by later results.

The earlier [five-configuration session](../../evals/library-runs/20260925-grounding-high/README.md)
retains its original failures. Its frozen awards rubric required optional job
competition/posting and scholarship-count details not requested by the question.
The latest audit corrects those two reference points in a new version, preserving
old annotations/scores. Under corrected factual scoring the previous high-effort
sample would reach 5/5, but its non-English status word still fails the project's
language requirement. It is not an accepted model configuration.

The new GPT-4.1 sample has all 11 question-aligned required points correct and all
19 inventoried factual claims supported. Personal abstention no longer adds an
unsupported contact. However, the awards answer still blends documents without
explaining their identity, so it fails the frozen named-source gate. One redundant
pass/fail prohibition also remains, a style miss. No more sampling was performed
to obtain a passing response. The full record includes both rubric versions.

Codex reviewed all outputs and source evidence as requested by the user. This is
not independent human review, but no requirement is imposed for the user to redo
all technical/source checking personally. These are repeated development cases,
not held-out accuracy, full-service reacceptance or general reliability guarantees.
The [evaluation plan](v1-evaluation-plan.md#review-and-release-gates) retains that
boundary. Earlier risks (list citations, CPT scope, API-setup rubric mismatch and
one invalid filename/source-line judgment) remain in the
[judgment supplement](../../evals/library-runs/20260925-review-supplement-3/README.md).

No broader retrieval features are needed. The remaining observed acceptance
issue is explicit document attribution when similar excerpts come from different
files. More general prompt reminders have not resolved it reliably. Future work
should target document-scoped evidence selection or explicit claim/source mapping,
with a separately defined contract and regression checks. This is a proposed next
step, not implemented behavior. Passing checks does not authorize merge; only
explicit user approval authorizes merging a v1 feature into `main`.
