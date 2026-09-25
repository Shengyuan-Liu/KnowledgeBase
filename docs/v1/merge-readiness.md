# v1 Merge Readiness — 2026-09-25

**The latest targeted verification does not pass: 3/5 cases pass after a scoped
prompt change. Source qualification remains unresolved under a conservative
reading, and a definite wrong-FAQ citation independently blocks unconditional
acceptance. No merge is authorized or performed.** See the
[fixed-context report](../../evals/library-runs/20260925-source-scope/README.md).
The original full-service acceptance remains 7/8 in its [acceptance report](../../evals/library-runs/20260925-v1-codex-acceptance/README.md)
and [actual answers](../../evals/library-runs/20260925-v1-codex-acceptance/REVIEW.md).
The user asked Codex to perform acceptance, so independent human review is not
being imposed as a prerequisite for Codex to deliver a functional verdict. The
review is explicitly labeled Codex-authored and not independent human validation.

## Completed evidence

- Markdown/TXT ingestion, structural parent-child storage, hybrid retrieval,
  optional local reranking, bounded evidence packing, source locations, restored
  diagnostics and file-deletion history have implementation and workflow checks.
- Last full backend run: 554 passed, 1 intentionally skipped live-provider test.
  Frontend: 40 passed. TypeScript/build passed. Browser workflows: 10 passed.
  [Records](../../evals/check-runs/20260925-retrieval-coverage/README.md) retain every
  failed attempt and correction, including Stop causing an unintended extra
  request when its DOM button was reused as Send. Distinct button identities fix
  that regression; the browser test asserts no extra request after cancellation.
- After the shared prompt change, [68 relevant tests passed](../../evals/check-runs/20260925-source-scope/README.md).
  These verify prompt delivery and generation/chat contracts, not semantic compliance.
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

## Current acceptance finding

The new eight-question run uses the checked-in defaults and a fresh isolated
index. All requests succeed, all six answerable cases receive complete annotated
evidence, both missing-information cases abstain, and latency/token budgets pass.
The actual answers were reviewed claim by claim against their supplied excerpts.

One answer says `anthropic-version` is "always ignored ... on all endpoints"
where the source table only says `Ignored`. The base status is correct; the
universal scope is not established by that excerpt. This is an unsupported
qualification judgment, not proof of contrary real API behavior. The frozen
scope/citation rules reject it. The run is retained as failed semantic acceptance,
not repaired or overwritten. The subsequent four-line scope instruction was
verified with five fixed-context generation calls, including this failure and
four controls. It removed the exact "always/all endpoints" wording, but the model
still said "in both cases". Conservatively the scope concern remains unresolved;
this is a debatable source interpretation, not proof the real API behaves otherwise.

More decisively, the scholarship answer cited the general FAQ for a separate-
application statement found only in the supplied admissions FAQ, then asserted
that every answer came from the general FAQ. This source/citation attribution
regression fails the frozen support gate even if the header wording is accepted.
Explicit pass/fail restrictions and both abstention controls pass. The five-case
result is 3/5, not a new full-service result or proof that the prompt caused the
regression. Same resolved model and contexts; one sample per prompt, with provider
variation uncontrolled. No judge calls, response repair or same-prompt retries.

The [existing evaluation plan](v1-evaluation-plan.md#review-and-release-gates)
distinguishes a functional release from demonstrated broad semantic improvement.
Independent human review remains unperformed and must not be claimed. Codex's
completed audit does not need to be relabeled human review to be useful, and the
user is not required to perform all technical or source checking personally.

Earlier development risks remain disclosed: list-level citation omissions, a
CPT qualification regression, the API-setup question/rubric mismatch, and one
invalid v11 filename-metadata assessment. These do not replace the new run's
specific findings or establish that its answers share every historical defect.

No broader features are needed. The next grounding change must address source
identity and exact table-status scope; another generic instruction alone has not
established the required behavior. Keep both failed attempts visible and
experimental options opt-in. Only an explicit user instruction authorizes merge.
