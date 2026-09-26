# Independent Planned Retrieval

Status: v2 stage 3a implemented as a standalone, offline-tested backend component.
It accepts a caller-supplied plan. Automatic LLM planning, evidence-dependent
queries, chat/API/CLI integration, saved conversation traces and sufficiency-driven
extra rounds remain subsequent work. Existing chat continues to use one query.
No live quality gain, feature acceptance or merge is implied.

## Contract and Module Responsibilities

| Module | Responsibility |
| --- | --- |
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
planner. Callers can serialize the whole result; this stage does not automatically
persist it in conversation history or publish progress events.

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
provider billing. No live controller is enabled in this stage. Before enabling
one, define planner input/output caps, total deadline, cancellation and final-answer
reserve, and measure actual provider calls including SDK retries.

## Trace and Coverage Boundaries

`PlanTrace` version 1 retains the plan, ready-file boundary, scope result, resolved
limits, executed query aliases, query-local diagnostics, exact candidate excerpts,
cross-query votes/ranks, selected IDs, requirement attribution and timings. The
returned `evidence` retains the exact supplied passages and budget exclusions.
Canonical offsets identify stable source spans; query ranks are not citation IDs.
Final answer source numbering belongs to the later application integration.

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
