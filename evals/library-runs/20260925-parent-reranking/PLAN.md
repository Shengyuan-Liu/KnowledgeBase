# Parent reranking acceptance

Purpose: address two observed semantic-child omissions while preserving default
structural ingestion and child reranking. No query decomposition or extra provider
query is introduced. Parent scoring groups the union of the original vector/BM25
routes by parent, uses the highest RRF child as representative, scores the exact
whole parent, then selects top K representatives. Flat chunks retain their text.

Freeze before outcomes: reuse the 17 documents, 24 questions and annotations,
canonical parents/children, saved vector top-20 and local model revision from
`../20260925T002400Z-semantic-acceptance/`. All questions are now development cases.
Repeat current BM25/RRF over the same SQLite snapshots. Reuse historical child
scores only after verifying exact scoring input, rank and question identity.
Score parent candidates with the same local BGE revision on MPS, batch four,
max pair tokens 2048 (1024 for old child control); no truncation. Parent total
input cap 32768 permits up to 20 whole parents; route windows remain 20, top K=5.

For both structural and semantic indexes, compare child/parent scoring at both
4096 and 6144 evidence tokens. Report each change separately, including
per-question regressions. 6144 is an explicit budget tradeoff, not a default change.
Use immutable source-span coverage as primary evidence metric and fixed-block
ranking proxies as secondary diagnostics. Do not compare child ranks across
chunking strategies as equivalent units. Candidate stages, selected children,
whole scoring regions and final evidence must remain separately inspectable.

This first phase is completed-component offline acceptance, using real local
reranking and saved vector observations. It does not remeasure embeddings,
ingestion, network/HTTP latency or generation. Local timings include warm MPS
inference but separate loading. Cached control scores cannot support latency
comparisons. Record every failure and all metric statuses.

Proceed to one scoped live generation comparison on the two original failed
questions only if final packed evidence improves without new coverage regressions
on the 21 answerable cases. Use the completed, unchanged generation prompt and
matched old/new retrieval contexts with the same answer model. Preserve complete
answers, evidence, usage and manual claim/point review by Codex (not independent
human review). Do not run another full judge benchmark merely to fill metrics.
