# Independent Planned Retrieval Verification — 2026-09-26

Scope: v2 stage 3a, caller-supplied plans and independent-query execution/merge.
Base commit `92a3b30`; each command JSON includes code-file hashes identifying the
working implementation. No automatic planner, live answer generation, feature
acceptance or merge is claimed. Raw attempts are retained unchanged.

## Checks

| Record | Outcome |
| --- | --- |
| `regression-1` | 51 existing retrieval, scope, packing and PDF tests passed after separating search from packing |
| `plans-1` | 17 passed, 1 failed: a new test fixture omitted the required `Chunk.index` field |
| `plans-2` | 72 passed, including 21 new plan/executor cases and the relevant regression suite |
| `backend-1` | 635 passed, 1 failed, 1 skipped: empty-library retrieval accidentally acquired packing diagnostics |
| `backend-2` | 636 passed, 1 skipped; pytest reported 20.56 seconds |
| `comparison-1` | Eight paired retrieval cases completed, 16 attempts total; no providers or model judge |

The fixture omission was corrected. The empty-library early return was restored,
preserving the existing test and response behavior. Existing Starlette/Pydantic
deprecation warnings and the optional live-provider skip remain visible.
Each `.json` contains command, timestamp, device, wall time, hashes and metric
inventory; `.log` contains the raw result. No frontend code was changed.

## Frozen Comparison

[fixture.json](fixture.json) freezes four source texts, complete binary relevance
labels, four questions/cases, query vectors and manually supplied plans. Cases cover
a direct question, independent requirements, a duplicate query, and insufficient
context budget. Run each under vector-only and hybrid retrieval, comparing the
preserved single-query control to the plan executor. This is a scoped offline
component check, not a full RAG evaluation.

Both variants use the same index, corpus, original question, labels, `top_k=2`,
context budget, tokenizer and retrieval options. Per-query candidate limit is 2;
reranking is disabled. Only supplied queries, cross-query merging and representative
selection differ. Embeddings and plans are hand-authored, with no automatic planner.
Baseline always runs first in one process; the first baseline includes cold
tokenizer loading. Latency is a diagnostic and cannot support a speedup claim.

Each document is one fully annotated canonical span and one child, so no changing
chunk boundary affects the comparison. Metrics below describe final selected
candidate order before expansion/packing, with K=2 (also the MRR cutoff).
Precision divides by K even with fewer results. NDCG uses binary gain and log2
discount; means are macro averages over four cases per strategy/variant. Final
coverage separately counts whole gold spans in the actual supplied context.

| Strategy / variant | Recall@2 | Precision@2 | Hit Rate@2 | MRR@2 | NDCG@2 | Final coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Vector / single | 0.750 | 0.500 | 1.000 | 1.000 | 0.807 | 0.625 |
| Vector / planned | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 | 0.750 |
| Hybrid / single | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 | 0.750 |
| Hybrid / planned | 1.000 | 0.750 | 1.000 | 1.000 | 1.000 | 0.750 |

Codex inspected all eight paired candidate orders and contexts against the frozen
texts. For the independent vector case, single retrieval supplies `a,c` while the
plan supplies `a,b`, increasing gold-span coverage from 1/2 to 2/2. Hybrid already
supplies `a,b`, so that case has no gain. Direct and duplicate-query results are
unchanged. The one-token budget supplies nothing in either variant even when both
relevant candidates were selected: retrieval success is not supplied-evidence
coverage. No measured per-case regression occurred in this small fixture.

[comparison-1-details.json](comparison-1-details.json) retains the fixture hash,
exact source spans, query/cross-query rankings, selected candidates, supplied
context, exclusions, limits, timing and per-case improvements/regressions.
[measurement-supplement.json](measurement-supplement.json) overrides the runner's
generic applicability for this comparison with the full measured inventory,
per-case observations and mean/P50/P95 timings (nearest-rank percentiles).
Stage samples include whole retrieval, query execution, embedding mocks, scope,
merge and packing. Separate search/fusion time is unavailable. Concurrency is one;
no sustained throughput or production capacity was measured.

No answers were generated, so correctness, faithfulness, completeness, relevance,
citation support/coverage and abstention are not applicable. Answer/first-delta
latency and provider token usage/cost are not applicable. Evidence token counts
are measured; local compute billing is unavailable. These results do not establish
real planning accuracy or a general RAG quality gain.

## Remaining Work

Automatic bounded planning, dependent-query evidence references, application
integration/persistence, progress/cancellation/deadline handling and sufficiency
assessment are subsequent stages. This executor accepts only independent plans;
its requirement lists are retrieval associations, not semantic support verdicts.
See [module guidance](../../../docs/planned-retrieval.md) for the usable contract.
