# v2 Branch and Scope Confirmation

## Change and Git State

The user requested that all subsequent v2 work be committed on `v2` and that OCR,
chart/figure understanding, and related advanced PDF interpretation be deferred.
Core digital PDF text, supported table extraction, and page citations remain in
scope. Update AGENTS.md and the design set consistently; no runtime code changes.

Created `v2` at existing design commit `c55ae35`. Restored the local `v1` reference
to accepted release `5f38974f38616f389d051108b85937b42172d2a9`, which is also the
unchanged `main` reference. The design commit remains preserved on `v2`. The
working tree was clean and no other worktree used `v1` before this operation.
No remote branch, merge, or push was changed.

## Review

Reviewer: Codex, model-assisted documentation review on 2026-09-26. Checked the
branch rules, PDF scope, frontend limitation copy, technical sequence, and
evaluation boundaries against the user's latest instruction. Deferred visual
understanding does not remove structured table extraction from the core feature.
The prior design review remains unchanged as historical evidence.

Run from the repository root:

```bash
node evals/check-runs/20260926T200634Z-v2-scope/review.mjs
```

The verifier reuses the previous documentation-check logic with this run directory
and AGENTS.md added to the reviewed files. Numbered JSON/log artifacts retain each
attempt, file hashes, base commit, duration, counts, and all measurement-policy
metric statuses. Content review found the branch and scope changes consistent.
Local links, formatting, and English-only text are checked by the verifier.
External references are unchanged; no new external factual claim requires a fetch.

All runtime metrics are `not_applicable`: no ingestion, retrieval, answer generation,
provider, or load behavior is exercised. Documentation-only changes require no
runtime test suite or paid evaluation. Source-level Mermaid review from the
original design remains the extent of diagram verification.
