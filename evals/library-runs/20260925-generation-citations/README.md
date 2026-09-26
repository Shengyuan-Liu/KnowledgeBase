# Claim-local citation and source-fidelity acceptance

This experiment evaluates the shared generation-prompt change committed at
`a829737`. The prompt requests a citation beside each factual statement or list
item, valid comments for source-derived code lines, preservation of explicitly
stated behavior, and evidence-backed guidance for missing personal information.
The change is implemented on `v1`; feature acceptance and merging remain the
user's decision.

On the **22 questions with valid assessments on both sides**, claim-local citation
coverage increased from 67.05% to 83.39%, while v11 faithfulness increased from
95.71% to 99.43%. This is partial improvement, not a complete fix: list citations
still fail on several questions, one answer strengthens a source's qualification,
and two new assessments timed out. Full-set quality acceptance remains incomplete.

## Controlled input and scope

The [plan](PLAN.md) and [freeze record](freeze.json) were committed before live
execution. The control is the previous
[structural parent-child batch](../20260925T002400Z-semantic-acceptance/parent_child/run.json):
24 questions, 17 frozen documents, identical annotations and exact supplied
excerpts. Every user message, including its source metadata and numbered text,
is reused byte-for-byte. Only the developer instructions change. No ingestion,
retrieval, query rewriting or reranking runs in this experiment.

The prior 24 answers and valid v11 reviews are reused. The new prompt generates
24 answers once, then each is assessed once under the same v11 hash, configured
judge model, high reasoning and four judge workers. Generation concurrency is
one; retries are zero. There is no calibration change or best-of-multiple-answer
selection. All 24 cases are development/regression data now, including the six
previously new cases. The split labels are retained only to align with history.

GPT-4.1 answers through the production `StreamingLLMClient`, using the same
saved-message shape as the production generator. Offline checks separately verify
that complete and streaming entry points receive the shared instructions. The
replay does not exercise HTTP transport, conversation persistence or the UI.

## Source review and remaining limitations

[REVIEW.md](REVIEW.md) inspects actual answers and supplied evidence. Tool-definition
items now each carry a citation, while the waiver and elective-approval answers
still cite only the final list item. The API field-support answer still introduces
“ignored” where the table says only which sub-field is supported. The personal
capstone answer removes undocumented channels for finding an assignment and cites
actual historical poster/team examples, which do not reveal this user's assignment.
A prompt request is not a guarantee
of compliance, and valid citation IDs do not establish support.

Inspection is by Codex, not an independent human reviewer. Judge disagreements
remain visible; no raw score, output or old artifact is overwritten to make the
change look successful. This experiment cannot establish general RAG accuracy or
fix the semantic-chunking retrieval regressions, because retrieval is frozen.

## Paired v11 assessment

All 24 new answers were saved. Twenty-two judgments are valid; the final assessment
calls for `msds-credits` and `msds-industry` each exceeded the configured 180-second
timeout after completing inventory and audit. Both failed attempts and successful
preceding stages are retained. No retry or regrading occurred. `run.json` therefore
remains `pending_reviews`, and full-set strict pass rate is unavailable.

The table uses only identical question IDs with valid, applicable assessments on
both sides. The two excluded questions are complex answers, so selection bias is
possible. A subset improvement cannot be presented as a full 24-question result.

| Assessment | Paired N | Before | After |
| --- | ---: | ---: | ---: |
| Expected-point correctness, normalized macro-average | 22 | 100% | 99.24% |
| Expected points attempted, regardless of truth | 22 | 100% | 100% |
| Faithfulness, supported inventoried claims | 22 | 95.71% | 99.43% |
| Claim-local citation coverage | 22 | 67.05% | 83.39% |
| Citation support, applicable on both sides | 21 | 96.67% | 98.21% |
| Relevance, normalized rubric | 22 | 100% | 100% |
| Appropriate abstention, unanswerable questions | 3 | 3/3 | 3/3 |
| Unjustified abstention, answerable questions | 19 | 0/19 | 0/19 |

The expected-point decrease is `api-setup`: the frozen rubric also requires
`anthropic.Anthropic()`, whereas the question asks which method invokes the model.
The new answer correctly names `client.messages.create()` but omits the constructor.
This question/rubric scope mismatch is documented, and the original score is kept.
The actual faithfulness regression is `msds-cpt-source-context`: “after the first
year” becomes “only” after it, with an additional smaller strengthening of a
referral for general information into a referral for detailed requirements.

V11 accepts the disjunctive unsupported/ignored wording and the new personal-schedule
answer; Codex retains narrower-wording concerns separately. These assessments
are not ground truth, and a high aggregate does not cancel concrete failures.

## Performance, usage and measurement boundaries

All 24 new generation calls completed; no request error, timeout or retry occurred.
The recorded generation window was 69.884 seconds including logging, or about
0.343 completed requests/second at concurrency one. This is not a load test.

Times below are seconds, n=24 per side, mean / median P50 / nearest-rank P95.

| Generation measurement | Historical control | New prompt |
| --- | ---: | ---: |
| SDK request to first nonempty answer delta | 0.636 / 0.625 / 0.960 | 1.013 / 0.789 / 2.159 |
| SDK request through stream close | 1.752 / 1.716 / 3.087 | 2.906 / 2.629 / 5.952 |
| Provider input tokens | 81,734 | 86,414 |
| Provider output tokens | 3,693 | 3,893 |
| Judge input tokens returned | 331,997 | 285,919 |
| Judge output tokens returned | 356,914 | 226,638 |

These are generation timings, not complete RAG-service latency. The baseline's
generation stage ran during the prior complete pipeline; the new run is standalone
generation. Provider/host load, cache state and time of day are uncontrolled, so
the single historical comparison does not establish a causal slowdown. There was
no warmup. The client host was macOS 26.6.2 ARM64; hosted model hardware and separate
provider queue-wait durations are unavailable. No local reranker was loaded.

The complete metric inventories explicitly mark ingestion, update/delete, model
loading, retrieval stages and full-service first-delta/completion as not applicable
to this replay. Old retrieval traces retain their original timings solely as
provenance; fresh per-answer service timing fields are null. Frozen ranking and
source-span coverage are retained and labeled historical. The same 21 answerable
cases have 99.967% supplied gold-character coverage in both groups; unanswerable
cases are excluded, not scored zero. Child units, K=5 and relevance labels remain
unchanged, with incomplete binary gold-overlap labels disclosed in each summary.

Billed dollars are unavailable; token counts do not establish a bill. Old usage
is historical and was not charged again by this replay. New provider calls are
limited to generation and judgment. The authorized existing `.env` was reused;
no credential or existing library was changed.
Judge usage is available for 70 of 72 new calls; the two timed-out calls have
unknown usage and cost, not zero. Reported output includes provider reasoning
tokens. Generation usage is available for all 24 calls. Resolved model revisions
remain `gpt-4.1-2025-04-14` for answers and `gpt-5.4-mini-2026-03-17` for judgments.
The new judge batch took 446.417 seconds at four workers. Per-question review
duration, including failed attempts but excluding worker queue wait, was
68.262 / 42.202 / 241.769 seconds (mean / P50 / P95, n=24). These are assessment
costs in time and are excluded from generation-response timings.

## Artifacts and verification

- [answers.jsonl](answers.jsonl): exact new text, supplied excerpts, source offsets,
  citation-ID checks and unchanged retrieval provenance.
- [calls.jsonl](calls.jsonl): exact request messages, resolved models, streaming
  deltas, timings, token usage and judge calls.
- [comparison.json](comparison.json): per-case changes and comparable aggregates
  for all cases and both historical splits.
- `before-*.json`: control summaries; their artifact names refer to the
  [baseline directory](../20260925T002400Z-semantic-acceptance/parent_child/).
  `after-*.json`: new summaries; their artifact names refer to this directory.
- [run.json](run.json), [collect.log](collect.log), [grade.log](grade.log): code,
  settings, timing scope, execution status and retained output.
- [offline checks](../../check-runs/20260925-generation-citations/README.md):
  67 scoped application checks and 3 replay preflight checks passed. The existing
  Starlette/AnyIO deprecation warning is retained.
- [final artifact audit](final-audit-1.json): 20 checks passed, covering unchanged
  inputs, exact answer-to-review hashes, source identity, model revision, complete
  error accounting, measurement scope, local links and absence of credentials.
  Passing this integrity audit does not complete the two timed-out judgments.

Use a new run directory for a later attempt. Passing checks or favorable aggregate
scores do not authorize a merge to `main`.
