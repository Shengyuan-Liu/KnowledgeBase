# New PDF questions: full-chain acceptance

**Result: 5/6 case gates pass.** All six HTTP/SSE requests complete, but one
answerable lecture question incorrectly withholds two facts that exist in the
PDF. This run does not close full-chain acceptance. No product code was changed,
no paid request was repeated, and no merge is authorized.

The six questions were frozen from original pages before calls and do not
duplicate the 19 unique questions in prior frozen case files. They use familiar
development PDFs, so this is not a held-out-document or statistical
generalization result. Unlike the preceding fixed-context acceptance, this run
exercises real planning, query embedding, retrieval, reranking, context packing,
assessment, supplementary retrieval, SSE generation and saved history.

## Quality and failure

| New case | Expected points correct | Result |
| --- | ---: | --- |
| Paper split boundary and rationale | 2/2 | Pass; physical pages 3 and 7 support the answer |
| Paper image format and companion files | 3/3 | Pass; physical page 3 |
| Lecture bag of words and learning counts | 1/3 | Fail; word order answered, two page-62 counts withheld |
| Exact lecture midterm date | No positive facts | Pass; appropriate local refusal |
| Current/non-current marketable securities | 3/3 | Pass; physical page 2, correct groups/date/units |
| Conditional operating/financing cash flows | 5/5 | Pass; physical page 3, correct years, comparison and outflow |

[Claim-level review](review.json) records **14/16 correct and complete expected
points**, **15/15 supported emitted factual claims**, **15/15 supported/cited
claims**, and relevance on 6/6 responses. Codex performed this review against
original rendered pages and actual supplied evidence; this is model review,
not human ground truth. Correct refusal is 1/1 on the unanswerable case.
Incorrect partial refusal is 1/5 on answerable cases; incorrect full refusal is
0/5. A claim-free refusal has no citation denominator. The financial condition
remains in factual requirements, with only `State the units.` in answering rules.
There is no unresolved-entity dependency in these questions.

The [lecture failure trace](failure-analysis.json) distinguishes an absent source
fact from an absent context fact. Both count bullets are correctly indexed on
physical page 62. The selected page-62 parent contains only the slide title;
the learning bullets belong to a different parent with a generic `Learning
phase` heading. The document-count child never reaches the retained candidate
lists. The word-count child reaches BM25 rank 17 and fused rank 32 for both
initial count queries, outside the 20-child rerank window. Two supplementary
queries do not recover either fact. No context-budget exclusion causes this miss.
The assessor's missing-context judgment and the answer's limitation statement
are faithful to what was supplied, but the user still receives an incomplete
answer. Loss of the slide title from the learning-count region is a plausible
contributor, not yet a causally verified repair target.

## Retrieval and performance

At K=5, final selected-child macro scores over five answerable cases are:
Recall **0.650**, Precision **0.200**, Hit Rate **1.000**, MRR **1.000**, and
NDCG **0.7233**. Selected-child fact-anchor recall is **0.760**. Final supplied
evidence contains **14/16** reference anchor groups. These use deliberately
limited source-anchor labels, not exhaustive semantic relevance; equivalent
page-7 wording and helpful neighboring context may be unlabeled. Parent
expansion can supply facts absent from the selected child. Candidate vector,
BM25, fusion and reranking scores remain separate in [diagnostics](diagnostics.json).
These scores are not comparable to the previous fixed-context workload.

| Timing, concurrency one | n | Mean | P50 | P95 |
| --- | ---: | ---: | ---: | ---: |
| First nonempty answer delta | 6 | 12.868 s | 13.503 s | 17.233 s |
| Complete HTTP/SSE response | 6 | 13.618 s | 14.431 s | 18.213 s |
| Query retrieval including embedding/rerank | 22 | 1.526 s | 1.402 s | 2.858 s |
| Query reranking | 22 | 1.180 s | 1.185 s | 2.226 s |
| Provider answer generation | 5 | 1.701 s | 1.867 s | 2.164 s |

Percentiles use linear interpolation. The first two rows include the local
refusal; it makes no answer-generation call. Startup was 5.154 s, excluded from
request latency. There were no warmup requests. Network/provider queue time is
included but not isolated. The six requests span 81.861 s, or 0.07330 completed
requests/s; this is not load capacity. Stage timings overlap and are not additive.
Vector search/BM25/fusion sub-timers are unavailable.

There were **44/44 completed provider calls**, zero errors, timeouts or retries:
6 plans, 10 assessments, 5 generations, 22 query embedding calls and one ingestion
embedding call. Responses used **68,491 input + 3,565 output = 72,056 tokens**,
including 2,304 reported cached input tokens. Embeddings used **3,036 tokens**.
Actual billed cost and embedding cached-token counts are unavailable. No paid
judge was used. Exact requests, supplied contexts, outputs, token usage and
rankings are retained in [server observations](server-observations.jsonl) and the
six case JSON files.

## Corpus, runtime and integrity

The source references are [DocLayNet](../../materials/pdf-v2/doclaynet.pdf),
[ML lecture](../../materials/pdf-v2/ml-lecture.pdf), and
[Apple FY24 statements](../../materials/pdf-v2/apple-fy24.pdf).
[Frozen cases](frozen-cases.json), [protocol](protocol.md),
[pre-call labels](frozen-labels.json) and [execution hashes](answer-execution-manifest.json)
retain source and annotation identity. Seven original pages were visually
inspected before calls; the additionally cited paper page 7 was reviewed
afterward without expanding frozen relevance labels. The missing-date label
uses full lecture digital-text search plus the logistics slide, not exhaustive
visual review of every embedded image.

Run HEAD is `3333d0f`; product implementation is unchanged since `5541597`.
Requested `gpt-4.1` resolved to `gpt-4.1-2025-04-14`; embedding model is
`text-embedding-3-small`. BGE reranking runs on MPS at revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` on macOS 26.6.2 arm64.
Apple parsing runs locally on CPU. [Resolved runtime](resolved-runtime.json)
and [index snapshot](index-snapshot.json) preserve all settings, parser versions
and model hashes, without credentials.

The stopped historical index was copied byte-for-byte under its owner lock.
The original remained unchanged. Its Apple file had been removed by an older
lifecycle test, so the same four-page PDF was uploaded into the clone in
**11.137 s**; lecture/paper extraction and embeddings were reused. The clone
holds five PDFs/98 pages, while questions explicitly scope three PDFs/88 pages.
Storage grew from 42,233,745 to 47,296,321 bytes after ingestion and 53,018,433
after answers; these totals include originals and conversation history, not just
vectors. Update/delete behavior was not exercised. Original PDF bytes, byte
ranges and revision binding pass for all three queried files. All six answers,
source payloads and retrieval traces match saved history. The evaluation server
is stopped, its port closed, and its ownership lock released.

The authoritative [20-metric inventory](measurement-v2.json) preserves all
applicable measurements and explicit gaps. The first offline report attempt
failed because it looked for `page_count` instead of the extraction's `pages`
list; [the failure](measurement-check.json) and [source](attempts/measure-v1.py)
remain. A subsequent report mislabeled the reranker as CPU; `measurement-v2.json`
corrects it from the recorded runtime to MPS and supersedes `measurement.json`.
It also marks embedding cached/output counters as unavailable/not applicable,
superseding diagnostic aggregation placeholders. No live data was changed or
rerun. Two scoped harness tests pass; final integrity and content/link review are
retained in `artifact-review.json` and `artifact-review.log`.

Next: isolate and repair the lecture title/body retrieval miss with scoped
offline controls, then use these same frozen questions, sources and annotations
for a matched feature acceptance. This result does not justify widening all
retrieval budgets or claiming general PDF reliability. Browser interaction,
unknown-entity dependent hops, OCR, visual charts and formula understanding were
not tested here.
