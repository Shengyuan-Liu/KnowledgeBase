# First-use new-PDF acceptance: two product failures

The six frozen questions yield **4/6 passing answer cases**, with **7/13 expected
positive points delivered**. Five requests complete and one returns a processing
error. The cross-paper answer is correct but uses independent searches, so the
separate dependent-execution gate is **not exercised**. Full acceptance fails.
No product implementation was changed, no answer was rerun, and no merge occurred.

## Frozen scope and execution

- Product commit: `377a577` on `v2`; implementation hashes match the original
  `7b93c61` preparation (runtime implementation `46d5931`).
- Inputs: [sealed four-PDF package](../../materials/pdf-v2-candidate-20261001/README.md),
  [six request-only questions](../../materials/pdf-v2-candidate-20261001/questions.json),
  [original-page references](../../materials/pdf-v2-candidate-20261001/references.json),
  [answer protocol](../../materials/pdf-v2-candidate-20261001/acceptance-protocol.md),
  and [browser protocol](../../materials/pdf-v2-candidate-20261001/browser-protocol.md).
- Four uploads, 90 physical pages, 566 child chunks/vectors and 145 parents.
  All original-byte, range and revision checks pass. All 12 unique reference
  facts map before any answer calls. No gold text enters the index or requests.
- Active isolated library: `data/evals/20261001-new-pdf-acceptance-2`.
  The initial empty startup attempt remains at
  `data/evals/20261001-new-pdf-acceptance`; neither is the user library.
- GPT-4.1 resolves to `gpt-4.1-2025-04-14`; embeddings use
  `text-embedding-3-small`. BGE reranker revision
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` runs on MPS; parsing runs on CPU.
  Evidence/assessment/generation caps are 4096/8192/16384 tokens.
- Six sequential planned requests, fresh conversations, zero SDK retries, no
  paid judge, answer repair or extra browser-generated answers. Existing credentials
  were explicitly authorized; no secret is recorded. Resolved configuration and
  environment-file digest are retained in [preparation](preparation-2.json),
  [runtime](resolved-runtime-2.json) and [execution freeze](execution-freeze.json).
- This set became **development material when the first results were inspected**.
  The sealed preparation is unchanged; this report records that status transition.

## Case review

| Case | Result | Positive points | Evidence and explanation |
| --- | --- | --- | --- |
| RAG document granularity | Pass | 2/2 | Same-document sequence versus per-token document choice, cited to original page 3 |
| Retriever training, both papers | Answer pass; dependency not exercised | 3/3 | DPR initialization and both negative types supported; two independent searches in one round, no binding |
| Retriever training, RAG only | Processing error | 0/1 | Bridge retrieved, missing recipe correctly recognized in raw assessment; malformed supplementary query aborts the response |
| Lecture overfitting | Pass | 2/2 | Correct definition and test-set effect; physical page 35 contains printed Slide 69 |
| Quarterly/annual operating income | Incorrect full refusal | 0/5 | All four planned queries treat `relevant document` as a literal document reference and return no candidates |
| Actual Q1 FY26 revenue | Pass | No positive facts | Appropriate refusal; forecast was not presented as actual revenue |

[Claim review](review.json) covers every required point and all **7 emitted factual
claims**. Those claims are faithful and have supporting inline citations (7/7);
this small emitted-claim denominator excludes the error and two claim-free
refusals and must not conceal incomplete answers. Semantic supplied-evidence
coverage is **7/13**, versus literal frozen-anchor coverage **6/13**: the full-hop
answer receives a valid alternate RAG initialization passage on page 5, rather
than the original page-3 anchor. The RAG source on pages 1-2 also supplies DPR's
name and pretrained context. Alternative support is documented, not added to
pre-answer ranking labels after seeing the result.

Appropriate full refusal is 1/1 on the unanswerable question. Incorrect full
refusal is 1/4 on fully answerable questions. The partial case delivers neither
its supported bridge nor its two required gap disclosures because the request
errors; an error is not successful abstention. The raw assessment distinguishes
available and missing points correctly, but it is not a delivered answer.

[Dependency review](dependency-review.json) retains both independent queries,
empty dependencies/bindings and the single retrieval round. The restricted
request's actual searches and retrieved candidates remain inside RAG; the
proposed DPR search is rejected before execution. This is observed scope integrity
before an abort, not successful partial-answer handling.

## Reproduced failures and next repair

[Offline reproduction](failure-reproduction.json) uses the exact retained model
output and retrieval result, with zero provider calls:

1. The restricted assessor emits a supplementary proposal with empty `target`
   and nonempty source references. `validate_assessment` raises
   `Question reformulations cannot contain an unbound target.` The live API
   exposes only `Answer processing failed.`; the local replay identifies the
   validator path, without claiming a live exception stack was recorded.
2. The financial planner starts each query with `In the relevant document, ...`.
   The document-reference resolver interprets `relevant document` as a file
   identity despite the explicit NVIDIA file boundary. All four searches produce
   `not_found`, no embedding/search results, and an incorrect all-missing refusal.

The next implementation step is a narrow repair with regressions from these two
retained failures: keep generic source wording within the already selected file
scope, and prevent an invalid optional supplementary proposal from discarding a
valid supported/missing assessment. Preserve real filename restrictions and
source-bound query validation. Do not repair the historical output or force a
plan to manufacture a dependency pass. A later live acceptance needs a new run;
this turn makes no component replacement comparison.

## Measurements

[measurement.json](measurement.json) records all 20 required metrics with scope,
counts, methods, aggregation and missing-data reasons. [diagnostics.json](diagnostics.json)
retains per-query vector/BM25/fusion/rerank metrics, final child selection, budget
exclusions, exact supplied evidence coverage, stage timings and usage.

| Measurement | Observed result |
| --- | --- |
| Final selected-child Recall@5 / Precision@5 | 0.625 / 0.200 |
| Hit Rate@5 / MRR@5 / NDCG@5 | 0.750 / 0.625 / 0.5967 |
| Ranking population | 4 available of 5 positive cases; failed partial case final selection unavailable, last observed retrieval retained separately |
| First answer delta | n=5; mean 8.279 s; P50 5.748 s; P95 15.221 s |
| Complete response | n=5; mean 9.129 s; P50 5.757 s; P95 16.699 s |
| Failed request terminal time | 12.444 s; no first answer delta |
| Upload-to-ready times | RAG 11.471 s; DPR 7.566 s; lecture 16.160 s; NVIDIA 13.414 s (rounded; raw values retained) |
| Request completion | 5/6; provider calls 28/28 terminal, no SDK errors/timeouts/retries |
| Provider call breakdown | 4 ingestion embeddings, 10 query embeddings, 6 plans, 5 assessments, 3 generations |
| Token totals | Ingestion embeddings 41,775; query embeddings 233; plans 11,958; assessments 22,237; generations 13,713 |
| Sequential completed throughput | 0.086 requests/s over 58.157 s; not load capacity |
| Storage | 9,750,565 bytes after ingestion; 12,498,981 bytes after shutdown including five saved conversations |

K=5 rankings use frozen full-anchor binary child labels, precision denominator
five, reciprocal rank truncated at five and log2 NDCG. The intended five-case
final-ranking macro cannot be measured after one request fails; the four-case
available mean is explicitly scoped. The financial empty ranking is an observed
zero; the failed request's missing final ranking is unavailable, not zero. Literal
labels are not exhaustive semantic judgments. Latency percentiles use linear
interpolation; network/queue time is included, startup and ingestion are separate.
Billed currency and isolated search/fusion/provider-queue times remain unavailable.
Update/delete and broad load testing are not applicable to this protocol.

## Browser observations

Visible Chromium **153.0.8010.12** was used at 1440x1000 and 390x1000; the exact
reported version is in [browser results](browser-navigation-result.json).
[Browser review](browser-review.json) records **8 passed, 2 partial and 2 blocked**
protocol items across both widths; full browser acceptance is not established.

- B1-B4 pass: real citation excerpts, physical page 35, navigation 35→36→35,
  close/reopen, and distinct RAG/DPR originals were inspected. Complete rendered
  canvas images confirm RAG page 5's initialization paragraph and DPR page 3's
  negative-training sentence. The source metadata and original bytes agree.
- B5 is blocked at both widths: the incorrect financial refusal has no citations.
  No replacement answer was generated to make this check pass.
- B6 is partial: saved answer/source/trace restoration matches actual API snapshots
  after reload and switching existing IDs. The product has no conversation picker;
  the harness sets its existing localStorage conversation key. No end-user picker
  is claimed. Dependency display is not exercised because the plan has no binding.
- All browser/history work leaves the SDK count at **28**. HAR files preserve GET
  requests; no new planning, embedding or generation occurred. Mobile controls
  work, but dense papers are very small at full-page fit; readability/zoom is not
  accepted by these checks.

Representative actual screenshots: [desktop page 36](visual-1440-lecture36.png),
[mobile page 35](visual-390-lecture35.png),
[mobile page 36](visual-390-lecture36.png),
[RAG complete canvas](visual-1440-rag-paper.pdf-page5-canvas.png),
[DPR complete canvas](visual-1440-dpr-paper.pdf-page3-canvas.png), and
[restored search plan](retry-1440-retriever-training-hop-history.png).

## Retained failures and limits

- First server startup's evaluation snapshot route was shadowed by the frontend
  static mount. No PDF or model call occurred. The original server/script/log/data
  remain; attempt 2 uses a separate empty directory and evaluation-only route order.
- Two pre-answer mapping scripts used nonexistent block field names. Both failed
  before writing labels; the third uses actual `source_ref` and maps 12/12 facts.
- Browser attempt 1 expected `data-rendered="ready"`, while the product uses
  `"true"`. Attempt 2 corrected that selector, but page-36 screenshots caught
  the loading state after a stale ready flag. A separate navigation check waits
  for changed canvas pixels and readiness; its screenshots were visually inspected.
  Earlier failed logs, traces and screenshots remain intact.
- An initial browser console resource 404 remains in the log; captured HAR files
  show no HTTP error entries. A shutdown semaphore warning remains in both server
  logs. The port is closed and both ownership locks are released.
- Reviewer is Codex (a model), not a human. Public source material may be familiar
  to model pretraining. One sample per question does not establish general accuracy,
  dependent-hop quality, a production SLA or a causal improvement over older tests.
- OCR, visual charts/figures, formula understanding, A-D ablations and release-wide
  regression acceptance remain outside this run. User acceptance and explicit
  feature-specific merge approval remain separate.
