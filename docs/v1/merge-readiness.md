# v1 Merge Readiness — 2026-09-25

**Do not claim full acceptance yet.** Current default GPT-4.1 passes 3/5 targeted
cases with the latest prompt. Alternative GPT-5.4-mini configurations reach 4/5,
but none clears the frozen gates. The
[correction-session report](../../evals/library-runs/20260925-grounding-high/README.md)
retains all five attempts and their actual answers. No model default, local `.env`
or merge has been changed. The user's model preference is pending; no tested
candidate currently qualifies for promotion.

## Completed engineering evidence

- Markdown/TXT ingestion, structural parent-child storage, hybrid retrieval,
  optional local reranking, bounded evidence packing, source locations, restored
  diagnostics and file-deletion history have implementation/workflow checks.
- Current full backend: **561 passed, 1 intentionally skipped live-provider test**.
  [Records](../../evals/check-runs/20260925-grounding-reasoning/README.md) include
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

In this session, explicit instructions, placement and model/reasoning comparisons
show different tradeoffs. The final high-effort sample has supported claims and
citations and avoids inappropriate contacts, but leaves out limited scholarships,
competitive positions and semester-by-semester postings required by the frozen
reference points. Its personal-status answer also contains a non-English word.
The unchanged factual rubric scores 4/5; language noncompliance is separately
reported. Do not relax the gates or attribute this candidate's gains to GPT-4.1.

Codex reviewed all outputs and source evidence as requested by the user. This is
not independent human review, but no requirement is imposed for the user to redo
all technical/source checking personally. These are repeated development cases,
not held-out accuracy, full-service reacceptance or general reliability guarantees.
The [evaluation plan](v1-evaluation-plan.md#review-and-release-gates) retains that
boundary. Earlier risks (list citations, CPT scope, API-setup rubric mismatch and
one invalid filename/source-line judgment) remain in the
[judgment supplement](../../evals/library-runs/20260925-review-supplement-3/README.md).

No broader retrieval features are needed. Further grounding work must address
source-specific completeness and English output; the bounded configuration
comparison has ended. Passing engineering checks does not authorize merge. Only
explicit user approval authorizes merging a v1 feature into `main`.
