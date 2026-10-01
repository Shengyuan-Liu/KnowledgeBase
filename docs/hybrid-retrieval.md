# Hybrid Retrieval

Status: integrated on `v1` for JSON chat, streamed chat, CLI, and the evaluation
runner. Hybrid retrieval is the default; user acceptance does not follow from
passing tests and merging still requires explicit approval. Optional
[reranking](reranking.md) is integrated before child selection.

## Query flow

1. Read the Ready-file IDs. An empty library returns no evidence without an
   embedding or generation request.
2. Search Chroma and score the SQLite child corpus with [BM25](bm25.md), each
   limited to `RETRIEVAL_CANDIDATE_LIMIT` (default 20). File eligibility applies
   before either limit and before lexical corpus statistics. Legacy flat chunks
   are included; parent text is never separately indexed or scored.
3. Apply equal-weight [RRF](rrf.md) to the union of both lists. Save the full
   fused ranking. When `RERANK_ENABLED=true`, score the leading
   `RERANK_CANDIDATE_LIMIT` candidates and order them by relevance, using RRF
   rank to break ties. Select `RETRIEVAL_TOP_K` (default 5) child/flat hits from
   the resulting order; with reranking disabled, select directly from RRF.
4. Expand parents, deduplicate by the highest-ranked selected child, and pack
   whole regions within the exact numbered `EVIDENCE_MAX_TOKENS` budget. The default
   `parent_then_child` policy tries a parent's whole child immediately when the
   parent does not fit, before considering lower-ranked evidence. Admitted parents
   represent all their selected children. PDF table parents instead wait until
   complete selected children are packed, then replace their siblings only if the
   full context fits without displacing unrelated retained sources. See
   [parent-child retrieval](parent-child-retrieval.md). Deduplication and budget
   exclusion can reduce the source count. No additional children are selected to
   fill unused slots, and source text is never truncated by retrieval.
5. Generate from the numbered evidence and save the completed answer, sources,
   and diagnostics together. Follow-up resolution precedes both retrieval routes.

Each query rebuilds lexical term counts from canonical SQLite chunks in one batch
read. New Ready uploads are immediately searchable, deleted and non-Ready files
are absent, and restarting needs no cached BM25 index. This simple approach is
intended for the current small library; large-library latency remains unmeasured.

## Configuration and controls

Use `.env` and restart the app:

```dotenv
RETRIEVAL_STRATEGY=hybrid
RERANK_ENABLED=false
RETRIEVAL_CANDIDATE_LIMIT=20
BM25_K1=1.2
BM25_B=0.75
RRF_K=60
RETRIEVAL_TOP_K=5
```

These are experimental starting values, not tuned quality guarantees. The route
limit and selected-child limit are independent: a small route union can yield
fewer than top-k candidates. `RETRIEVAL_STRATEGY=vector` uses the earlier vector
path with `RETRIEVAL_TOP_K` directly; it does not build lexical statistics and
requires reranking to be disabled.
Changing retrieval settings does not change stored chunks or require re-embedding.
API, CLI, and evaluation entry points pass the same `Settings.retrieval_options`
to the services. Pure calls accept `RetrievalOptions` without loading credentials.

For an isolated evaluation using the standard evaluation corpus:

```sh
uv run --locked python -m evals.evaluate run --label "Hybrid control" \
  --retrieval-strategy hybrid --no-rerank --retrieval-candidate-limit 20 --rrf-k 60 --top-k 5
```

The runner also supports `--bm25-k1` and `--bm25-b`, and records resolved options
in `run.json`. This command makes provider calls. Use a matching vector run for
comparison; compare exact supplied evidence and answers, not RRF magnitudes.

## Evidence and diagnostics

- `retrieval.options` and `top_k` record the query-time configuration.
- `vector_matches`, `bm25_matches`, and `fused_matches` retain route IDs, raw
  scores, and ranks, including hits outside the final selected top-k.
- `candidates` contains only the selected child/flat hits, with exact text and
  offsets. Each candidate's `fusion` records its original RRF rank and route
  provenance; optional `rerank` adds a distinct relevance score and rerank rank.
- `rerank` retains the full scored window, exact child text, all relevance scores,
  model, prompt version, and limits. `rerank_seconds` records scoring-stage time.
  Both fields are null when scoring is disabled.
- `excluded` records selected hits absent from final evidence in the default mode;
  `unexpanded_parents` records omitted parents whose children remain represented.
  `parent_first` retains the earlier whole-region exclusions.
- `packing_seconds` records evidence-packing time;
  `evidence_tokens` counts the final numbered text actually given to generation.
- Each source's `fusion` describes its highest-ranked selected child. Its
  `distance` is null when that child is absent from the vector candidate window.
  Missing route values are never replaced by zero. Other selected sibling hits
  remain inspectable in `candidates` and `matched_child_ids`.

The source panel retains exact parent text; its existing debug section shows
RRF, route, and optional rerank ranks and handles missing vector distances. Scores are not confidence
probabilities. JSON snapshots retain this metadata across restart and deletion.
Older snapshots lacking fusion/options/rerank remain readable without inferring
old ranks. With reranking disabled, full child text is saved only for selected
candidates. With it enabled, the scored window also retains exact inputs, even
when a candidate is not selected or its parent is excluded by the evidence budget.

## Verification

`tests/test_hybrid_retrieval.py` checks consensus ranking, separate route windows,
vector controls, Ready-only corpus statistics, lexical-only parent evidence,
exact budgets, JSON/SSE, restart without re-embedding, deletion, and saved history.
Runtime tests verify nondefault settings reach API/CLI/evaluation. Frontend tests
cover null distances in both streamed and restored answers. Existing parent
deduplication, source fidelity, and no-generation-without-evidence tests still apply.

The [live paired comparison](../evals/library-runs/20260923T221737Z-hybrid/README.md)
records 36 real-provider answers. GPA and CPT improve, while prerequisite evidence
is displaced by larger FAQ parents. Overall span coverage improves modestly;
the [subsequent rerank comparison](../evals/library-runs/20260924T000238Z-rerank/README.md)
checks that regression and the rest of the same 18-question set.
