# v1 Merge Readiness — 2026-09-26

**The document-scope implementation is complete; full acceptance is still not
passed.** [The final comparison and retained recovery](../../evals/library-runs/20260925-document-representation/README.md)
show that the observed cross-document attribution defect is fixed. Both FAQ
sources now reach the model, comparison gold-span coverage is 100% (previously
50%), and the answer names Admissions correctly. Requested single-document
questions use only the resolved document's evidence. Ambiguous or missing names
produce clarification without query embedding or generation.

The first pass completes 10/11 service requests and passes 9/11 frozen strict
reviews. One stream times out; one comparison omits the explicitly required
statement that General FAQ lacks the policy. The bounded recovery completes the
timeout question correctly in 2.89 seconds. Combining attempts gives 11/12 service
completions and 10/11 distinct strict passing cases, **not** a clean 11/11 pass.

Successful-request mean latency is 10.443 seconds, P95 completion 46.242 seconds,
and P95 first answer delta 38.993 seconds, exceeding the frozen 10/20/10-second
gates. The failed stream takes 62.179 seconds to terminate. Delay is inside model
generation; traces do not establish whether its cause is upstream processing,
network behavior or host scheduling. The failed request also lacks final token
usage/billing. One successful recovery does not prove these operational issues
resolved. No unconditional merge recommendation is made on this evidence.

## Completed engineering evidence

- TXT/Markdown ingestion, structural parent-child storage, hybrid retrieval,
  optional local reranking, bounded evidence packing, source locations and
  saved diagnostics/history have implementation and workflow checks.
- [Document scope](../document-scope.md) filters files before vector/BM25 ranking.
  Explicit multi-file requests prioritize a representative per file when capacity
  permits, before additional same-file hits. Resolved title labels are included in
  budgeted source metadata and historical snapshots. No schema migration or
  reindex is needed for this change.
- Final backend: **589 passed, 1 intentionally skipped live-provider test**.
  Frontend unit tests: **42 passed**. TypeScript/production build passes.
  All 12 distinct browser scenarios passed across retained runs: the original
  ten passed in the initial browser run; both scoped workflows passed after the
  final representation change. This is not one final 12-test browser invocation.
  [Records](../../evals/check-runs/20260925-document-scope/README.md) retain earlier
  command/fixture failures, source offsets, API/streaming parity, explicit file
  IDs, follow-up, restored scope, deletion and exact metadata token budgets.
- Final artifact audit: seven checks pass, including identical failed/recovery
  provider messages and product hashes, source-review quote offsets, preserved
  partial output/error, both FAQ representatives and unchanged failed gates.
  These are evidence-integrity checks, not additional paid quality sampling.
- The previous [real-provider UI workflow](../../evals/browser-runs/20260925-semantic-ui-1/README.md)
  predates document-scope changes. Current UI checks use mocked providers; the new
  live acceptance exercises the production service without HTTP/browser transport.

## Configuration and limitations

Defaults remain structural `parent_child`, hybrid retrieval, child scoring,
4096-token packing, GPT-4.1 and omitted `ANSWER_REASONING_EFFORT`. Local reranking
stays disabled unless enabled. Local `.env` and model defaults were not changed.
Semantic chunking and parent scoring remain opt-in experiments; their
[coverage/compute comparison](../../evals/library-runs/20260925-parent-reranking/README.md)
does not justify promoting them to defaults.

Scope recognition has an explicit bounded syntax, not arbitrary natural-language
understanding. More files than top-K or a tight context budget can still leave
requested evidence out. Exact API `file_ids` disambiguate identical names; the UI
shows scope diagnostics but has no new file picker. Follow-up resolution retains
its existing model dependency; explicit API file IDs apply to that request only.

Codex reviewed every output and source claim as authorized. This is implementer
review, not independent human review, held-out accuracy or a general reliability
guarantee. No requirement is imposed that the user personally repeat all source
checking. The original [7/8 service run](../../evals/library-runs/20260925-v1-codex-acceptance/README.md),
[4/5 prompt correction](../../evals/library-runs/20260925-answer-focus/README.md),
and [10/11 initial scope run](../../evals/library-runs/20260925-document-scope/README.md)
remain unchanged. The [judgment supplement](../../evals/library-runs/20260925-review-supplement-3/README.md)
retains older rubric and judgment limitations.

## Acceptance decision still required

No more broad retrieval work is indicated by this sample. Outstanding gates are
explicit contrast completeness, latency/reliability and missing failed-call usage.
The comparison's main answer is correct, but its frozen additional point must not
be silently waived. Do not rerun paid sampling until green or add speculative
retry/fallback behavior. Any future acceptance-criteria change must be explicit,
prospective and retain these results. Further performance diagnosis should first
use the retained call timings and stream deltas.

All work remains on `v1`. No feature merge is authorized. The user decides whether
to accept known limitations and gives explicit feature-specific merge approval;
passing engineering checks alone does not permit merging into `main`.
