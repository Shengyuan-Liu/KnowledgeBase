# Independent Planned Retrieval

Status: v2 stage 3b integrates the independent executor with opt-in automatic
planning in JSON/SSE chat and CLI. Completed answers retain their plan and exact
evidence. Offline checks cover integration and request bounds; live planner and
answer quality remain unmeasured. Evidence-dependent queries and sufficiency-driven
extra rounds remain subsequent work. No feature acceptance or merge is implied.

## Contract and Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `providers/planner.py` | Make one strict structured-output call and validate its direct/decomposed/narrowing decision |
| `services/planning.py` | Freeze ready-file scope, track deadlines/cancellation and reserve answer time |
| `rag/planning.py` | Validate an original/resolved question, required answer points and independent query records |
| `direct_plan` | Construct the existing single-query route without calling a model |
| `rag/retrieval.py: retrieve_candidates` | Resolve Ready-only scope and return bounded, unpacked child hits with query-local scores |
| `resolve_ready_scope` | Resolve document references within an allowed ready-file catalog |
| `pack_retrieval_candidates` | Expand selected children, attach PDF provenance and pack one final context |
| `rag/planned_retrieval.py: retrieve_plan` | Execute queries sequentially, merge/select candidates and return evidence plus a versioned trace |
| `merge_query_runs` | Combine query ranks while keeping this merge separate from within-query BM25/vector RRF |

`RetrievalPlan` permits one to six requirements and one to six independent query
records. Requirement/query IDs are unique; queries must reference existing
requirements and collectively address all of them. A direct plan queries the
resolved question exactly once. Unknown fields, including dependent-query fields,
are rejected. These bounds reject oversized plans instead of dropping tasks.
Requirements express intended answer coverage; they do not establish support.

```python
from knowledgebase.rag.planning import AnswerRequirement, PlannedQuery, RetrievalPlan
from knowledgebase.rag.planned_retrieval import retrieve_plan

plan = RetrievalPlan(
    original_question="Describe the training method and evaluation results.",
    resolved_question="Describe the training method and evaluation results.",
    route="decomposed",
    requirements=[
        AnswerRequirement(requirement_id="method", description="Training method"),
        AnswerRequirement(requirement_id="results", description="Evaluation results"),
    ],
    queries=[
        PlannedQuery(query_id="method-query", text="training method",
                     requirement_ids=["method"]),
        PlannedQuery(query_id="results-query", text="evaluation results",
                     requirement_ids=["results"]),
    ],
)
# Reuse the application's existing session and clients; the caller owns them.
result = retrieve_plan(plan, session, embeddings, store, file_ids=selected_file_ids)
context_chunks = result.evidence.chunks
trace_json = result.model_dump_json(indent=2)
```

The example assumes an open session, existing clients and an explicit file
selection. It does not create credentials, a provider client or an automatic
planner. The lower-level function returns its result; the chat integration below
adds planning, persistence and progress events.

## Execution, Ranking and Scope

1. Resolve the user's original/resolved question and explicit file selection
   against Ready files. Keep that catalog as the boundary for all subqueries.
   Unknown/ambiguous user scope stops without embedding calls. A query's explicit
   file list must be a subset; a scope-expanding plan raises before any query runs.
   Textual subquery references are resolved inside the boundary. An empty list
   means no files, never unrestricted retrieval.
2. Execute independent queries sequentially. Identical trimmed query text and
   equivalent requested file sets share one execution and retain all query IDs
   and requirement associations. Provider failures propagate; the executor has
   no retry or response-repair loop. Existing injected provider retry settings
   remain the caller's responsibility.
3. Use the existing vector or BM25/vector path and optional reranker. For decomposed
   plans, each query returns at most `RetrievalOptions.candidate_limit` children
   in its own fusion/rerank order. Direct plans retain the existing `top_k` path,
   including explicit-document prioritization. No per-query context is packed.
4. Merge by stable child ID with `sum(1 / (rrf_k + query_rank))`. Equal scores break
   ties by child ID. Within-query scores stay in the query trace. Repeated query
   text contributes at most one vote per child even across different narrow scopes;
   use its best rank across those executions. The cross-query merge uses the
   configured `rrf_k` (default 60), recorded separately from within-query fusion.
5. Reserve a representative for each requirement/document group in round-robin
   requirement order where candidates and `top_k` permit, then fill by merged rank.
   A candidate already selected can represent another group. This is retrieval
   diversity, not a semantic claim that the requirement was answered. Final order
   may differ from pure merged score order; both orders are retained.
6. Expand and deduplicate parents once, then pack one context using the existing
   strategy and budget. Preserve canonical slices, source labels and PDF page/table
   provenance. Supplementary PDF headers and metadata count toward that budget.
   Whole parents or child fallback regions may still be excluded by the budget.

The default final budget stays 4096 tokens and default final child selection stays
`top_k=5`. Six query records bound logical query executions, not request time or
provider billing. The automatic integration adds the bounds below; calling the
standalone executor directly leaves timeout/retry policy to its caller.

## Trace and Coverage Boundaries

`PlanTrace` version 1 retains the plan, ready-file boundary, scope result, resolved
limits, executed query aliases, query-local diagnostics, exact candidate excerpts,
cross-query votes/ranks, selected IDs, requirement attribution and timings. The
returned `evidence` retains the exact supplied passages and budget exclusions.
Canonical offsets identify stable source spans; query ranks are not citation IDs.
The chat service numbers final packed sources once, before publishing citations.

For each requirement, the trace distinguishes candidate, selected, supplied and
budget-excluded child IDs. These lists refer to that requirement's own query hits;
parent expansion can include additional text without proving new semantic support.
There is no `supported` verdict, confidence score or fabricated explanation.
An executed query with unresolved scope has an empty result and its scope status.
Stop reasons describe completion of this independent batch, not answer sufficiency.
Exceptions propagate without returning a successful partial trace.

## Verification

The [run record](../evals/check-runs/20260926-planned-retrieval/README.md) retains
unit/regression checks, failed attempts, and a frozen before/after retrieval fixture.
Tests cover direct-route compatibility, scope confinement, empty/unready catalogs,
query deduplication, RRF ties, requirement fairness, shared parents, PDF context,
one global budget and trace serialization. No provider calls or LLM judging are used.

The frozen fixture has hand-authored plans/vectors and complete binary labels for
four source spans. It compares selected candidate metrics separately from final
context coverage. Its vector baseline misses one independent fact that the planned
route finds; its hybrid baseline already finds both, so it shows no quality gain.
These results validate mechanisms, not real planning or answer quality.


## Automatic Planning and Chat

Select **Plan complex questions** above the chat composer. The checkbox defaults
to off on each page load and sends an explicit `retrieval_mode` for each request.
The evidence panel shows **Search plan**, executed queries and which answer points
have retained passages. This is retrieval attribution, not semantic sufficiency.
JSON and SSE requests accept `"retrieval_mode": "planned"` or `"single"`; omitted
values use `RETRIEVAL_MODE` (default `single`). CLI accepts `--retrieval-mode planned`.
The existing evaluation runner does not yet select this controller automatically.

1. Resolve follow-ups from completed history using the existing resolver.
2. Resolve original/resolved document references and explicit `file_ids`. Snapshot
   Ready files before planning; newly uploaded files cannot widen that boundary.
   Empty or unresolved scope skips the planner and preserves the existing response.
3. Call `PLANNER_MODEL` once, defaulting to `ANSWER_MODEL`, using strict Responses
   API JSON schema. The configured provider/model must support
   [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
   No compatibility fallback, repair, second planning attempt or guessed intermediate
   facts are introduced. A direct decision searches the resolved question unchanged.
4. Validate up to six requirements and six independent queries. Original/resolved
   questions are set by the application; the model cannot override them or file IDs.
   A `needs_narrowing` decision returns a fixed request to split the question without
   searching or generating. Invalid/incomplete output fails without saving a turn.
5. Execute the batch, pack one context, publish final numbered sources and generate
   one answer. Requests requiring evidence-dependent hops currently use a direct
   search; dependency resolution and sufficiency loops are not implemented.

`retrieval.planning` version 1 persists inside the existing diagnostics snapshot;
no database migration or reindex is needed. It includes planner prompt/output,
requested/resolved model, response ID, actual usage when provided, limits, exact
supplied context and the executor trace. JSON answers, SSE `sources`/`complete`
and restored history share that record. Deleted files keep their historical text
and plan; original PDF availability follows the existing deletion contract.

SSE adds `progress` with `stage=planning` or `retrieving` and a public message.
These events contain no provisional citations. The final `sources` event follows
all searches. Cancellation or failure before the final save never saves a partial
answer. As before, disconnecting after the final transaction begins may lose the
completion event for a fully saved answer; reload before retrying.

## Request Bounds

The nested environment fields use `PLANNING__` in [.env.example](../.env.example).
They apply only to planned requests. Single-search behavior and its configured
SDK retries remain unchanged.

| Setting | Default | Meaning |
| --- | --- | --- |
| `PLANNING__REQUEST_TIMEOUT_SECONDS` | 180 | Overall controller deadline from before history loading |
| `PLANNING__ANSWER_RESERVE_SECONDS` | 60 | Stop planning/search before this final-answer time reserve |
| `PLANNING__PLANNER_TIMEOUT_SECONDS` | 30 | Planner SDK timeout, also capped by remaining search time |
| `PLANNING__MAX_INPUT_TOKENS` | 8192 | Per-call serialized planner input/schema or resolver-message cap |
| `PLANNING__MAX_OUTPUT_TOKENS` | 2048 | Planner/resolver output cap |
| `PLANNING__ANSWER_MAX_INPUT_TOKENS` | 16384 | Serialized final-answer message cap |
| `PLANNING__ANSWER_MAX_OUTPUT_TOKENS` | 4096 | Final-answer output cap |

Local input counting uses `CHUNK_TOKENIZER`; it is not exact provider billing or
message-framing usage. Output caps are sent to the provider. Evidence retains its
separate `EVIDENCE_MAX_TOKENS` budget. There is no monetary spending cap. Planned
resolver, planner, query embeddings and final generation use zero SDK retries.
Limits bound each call and batch; duplicate queries share an execution.

Streaming waits for planning/search and final provider events respect the remaining
wall-clock deadline. Sync JSON/CLI stages check the deadline between operations and
bound each provider timeout; they cannot forcibly interrupt local CPU work or a
blocking transport. An already in-flight sync request may finish after Stop or a
timeout, potentially consuming provider tokens. Cancellation checkpoints prevent
later queries, generation and persistence. The final short save transaction retains
its existing cancellation semantics. Deadline errors use JSON HTTP 504 or an SSE
`error`; other model/validation failures use the existing generic error.

The saved planner usage comes from the actual response when available; billed cost
is explicitly unavailable. Resolver/embedding/final-answer usage is not yet captured
by this trace. Live acceptance must instrument those calls before making whole-turn
cost or performance claims.

## Stage 3b Verification

The [automatic planning run](../evals/check-runs/20260926-automatic-planning/README.md)
retains backend/frontend/browser checks and a paired replay of the exact stage 3a
frozen corpus, questions, annotations and vectors. Planner responses are mocked
hand-authored plans. Candidate metrics and final coverage match stage 3a; this
validates integration, not the model's ability to plan or produce correct answers.
The record preserves failed collection/runner attempts and remaining measurement gaps.
