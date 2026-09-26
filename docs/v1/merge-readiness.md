# v1 Merge Readiness — 2026-09-26

**The current default v1 path is ready for user acceptance and a feature-specific
merge decision.** The [single awake-host acceptance](../../evals/library-runs/20260926-comparison-awake/README.md)
passes all 11 service requests and all 11 frozen strict reviews on its first pass.
Every required v2 answer point is present; all 26 inventoried factual claim units
and associated citations are supported. Seven answerable questions have full
annotated source-span coverage. Comparison explicitly addresses both FAQs.

Mean service completion is 1.757 seconds, nearest-rank P95 is 4.016 seconds, and
P95 first answer delta is 3.596 seconds. Both active and wall clocks meet the
original gates. Nine generations and nine query embeddings succeed, with zero
SDK retries or judges and complete reported token usage. Dollar billing remains
unavailable. This is a bounded sample, not a general latency or accuracy guarantee.

## Diagnosis and completed correction

The [previous run](../../evals/library-runs/20260925-document-representation/README.md)
retains its two slow completions, timeout, incomplete comparison and failed gates.
All three anomalous generation starts align with actual host sleep events in the
[diagnosis](../../evals/check-runs/20260926-generation-diagnostics/README.md).
This confounds prior performance measurements; it does not prove every old delay
was caused solely by sleep. The new batch ran under a temporary sleep-prevention
assertion, with no power transitions recorded and under 0.00003 seconds maximum
service clock divergence. No daily power, model, timeout or retry setting changed.

Document scope already filters files before vector/BM25 ranking, prioritizes
representatives for explicit multi-file requests when capacity permits, and carries
budgeted identity labels into context and history. The final correction specifies
one item per named document and preserves this through the brevity instruction.
It adds no hardcoded source facts, output repair, fallback or extra model call.
Evaluation now records both clocks and stream-open timing to expose suspension.

## Engineering and evidence

- Backend: **593 passed, one intentionally skipped opt-in live-provider test**.
  Scoped implementation checks: 75 passed. Subsequent stream-cleanup checks: 12
  passed, including 25 sequential real-SDK/mock-HTTP streams with forced collection.
  [Records](../../evals/check-runs/20260926-generation-diagnostics/README.md) retain
  commands, code hashes, durations and metric applicability.
- Latest frontend unit evidence remains 42 passed; TypeScript/build passes;
  all 12 distinct browser scenarios passed across retained runs. No frontend
  implementation changed in this correction. These are not newly rerun checks.
  [Scope workflow records](../../evals/check-runs/20260925-document-scope/README.md).
- Current live acceptance exercises production streaming service, persistence,
  original questions and source evidence; it excludes HTTP/browser overhead.
  Final artifact checks verify exact quotes, frozen references, both clocks,
  provider call limits, and saved answers/evidence/diagnostics for all 11 requests.
- The previous [real-provider browser workflow](../../evals/browser-runs/20260925-semantic-ui-1/README.md)
  predates the scope/prompt changes. Current scope UI checks use mocked providers.
- TXT/Markdown ingestion, parent-child storage/retrieval, hybrid search, evidence
  packing, citations, follow-up, restoration and deletion retain their prior
  implementation and workflow checks. No migration/reindex is needed here.

## Known limits to accept

One non-fatal async-generator finalizer warning remains in the live run log:
`BoundAsyncStream.__aiter__: ValueError: async generator already executing`.
All requests completed and their snapshots were verified. The warning did not
reproduce in the scoped offline stress check; its live-transport cause remains
unresolved. There is no observed request failure or missing saved answer from it,
but no general resource-leak or zero-warning guarantee is made. Keep it visible
for follow-up rather than suppressing it or changing dependency internals.

Some answers repeat conclusions. Comparison absence is worded page-wide, matching
the inspected frozen file but broader than the prompt's desired excerpt-level
wording. These are style/wording limits, not changed factual review criteria.
Codex reviewed every claim and expected point; this is implementer review, not
independent human review or held-out quality. The user does not need to repeat
all source checking personally.

Defaults remain structural parent-child, hybrid retrieval, child scoring,
4096-token packing, GPT-4.1 and omitted reasoning effort. Local reranking is off.
Semantic chunking/parent scoring remain opt-in experiments; their earlier
[coverage/compute comparison](../../evals/library-runs/20260925-parent-reranking/README.md)
does not justify promotion. PDF, agents, load capacity and broad release accuracy
are outside this recommendation.

Scope recognition is bounded syntax. Top-K and context budgets can omit requested
files/facts. Exact API file IDs can disambiguate names; there is no new UI picker.
Follow-up resolution remains model-dependent; explicit API IDs apply per request.

## Merge decision

Recommend accepting the implemented default v1 functionality with these recorded
limitations. Do not add more retrieval work or repeat paid sampling to erase
historical failures. Original 7/8, 4/5, scope failures and the separate timeout
recovery remain intact; the new pass is its own evidence under unchanged references.

All work remains on `v1`. This recommendation is **not authorization**: only the
user's explicit feature-specific approval permits a merge into `main`.
