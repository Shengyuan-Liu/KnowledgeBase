# BM25 library replacement

The hand-written term statistics and scoring loop are replaced by
[BM25S 0.3.11](https://pypi.org/project/bm25s/0.3.11/). Its
[public scoring configuration](https://github.com/xhluca/bm25s/blob/a213158181d4b3781ba06bc88840f89871f1c775/bm25s/__init__.py)
supports independent term-frequency and IDF methods. ATIRE term frequency plus
Lucene IDF preserves this application's existing formula. Scores use float64.
The default `rank_bm25.BM25Okapi` has a different IDF/floor convention and would
change common-term and single-document behavior; see its
[implementation](https://github.com/dorianbrown/rank_bm25/blob/master/rank_bm25.py).

The local adapter retains canonical tokenization, unique query terms, Ready-file
scope supplied by the caller, omission of tokenless/nonmatching chunks and stable
chunk-ID ties. No cached index or migration is added; deletes and scope changes
take effect on the next query. BM25S's only required dependency is NumPy, already
installed in this project. No existing dependency versions change; uv also
refreshes dependency platform markers in the lockfile.

## Frozen comparison

`bm25-workload.json` was frozen before either run: the existing 25 NYU questions,
16 verified source files, 64 parent-child retrieval chunks, original source-span
annotations, K=5/20, k1=1.2, b=0.75. Both arms use identical serialized children
and the existing `evals.metrics.ranking` implementation. The old scorer remains
only as `bm25-before.py` in this historical run, not as a production fallback.

All 25 top-20 candidate orders match exactly. The largest score difference is
`7.105427357601002e-15`, below the predefined absolute tolerance `1e-10`.
All per-question measured quality values match; no measured ranking improvement
or regression occurred.

| Metric | K=5, both arms | K=20, both arms |
| --- | --- | --- |
| Recall | 0.875 | 1.000 |
| Precision | 0.200 | 0.060 |
| Hit rate | 0.900 | 1.000 |
| MRR with cutoff K | 0.82917 | 0.83711 |
| NDCG | 0.83072 | 0.86936 |

Quality averages use 20 answerable cases; five unanswerable cases have no ranking
ground truth and are excluded. Relevance is binary overlap with annotated source
spans, not exhaustive semantic labels. Precision divides by K even when fewer
results exist. These values describe only lexical candidates, not final evidence.

| Local stage timing, n=25 | Before | BM25S |
| --- | --- | --- |
| Mean | 2.976 ms | 5.150 ms |
| P50 | 2.979 ms | 4.916 ms |
| P95 | 3.106 ms | 5.259 ms |

Timing includes tokenization and rebuilding the temporary index, excludes imports,
model loading, queue waiting and corpus preparation. Concurrency is one; one warm
process pass per arm, no warmup requests, uncontrolled host load. Both arms complete
25/25 calls with no errors or retries. The small index is rebuilt per query, so
this replacement reduces custom code but does not claim a speed improvement.

Raw outputs are `bm25-before.json` and `bm25-after.json`; the complete 20-field
inventory and per-case comparison are in [measurement.json](measurement.json).
No provider calls, generated answers, billed cost, final evidence packing or
production load were measured. Existing high-level regression tests separately
cover scope, deletion, packing, citations and saved history.
