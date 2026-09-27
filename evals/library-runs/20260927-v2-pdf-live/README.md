# Live PDF development acceptance: failed gates, targeted repair

On 2026-09-27, the production HTTP/SSE routes ingested five original PDFs (98
physical pages) and ran 16 frozen questions in both single and planned modes.
After preserving the initial pass at `3106e06`, one targeted repair and one paired
replay were performed on the same index. **This does not pass development
acceptance and is not a release or merge recommendation.**

The repair improves planned completion from **9/16 to 15/16** and requested-point
correctness from **42.86% to 80.00%**. However, repaired single mode scores 87.14%,
planned mode still fails one request and incorrectly abstains on an answerable
financial comparison, and table/citation support issues remain. A completed SSE
response or valid citation ID does not establish correctness.

## Frozen workload and comparison limits

- [Protocol](protocol.md), [original cases](frozen-cases.json), and
  [effective cases](effective-cases.json): 16 turns, including one follow-up,
  papers/lecture/financial and technical reports, dense/merged tables, partial
  answers, source restriction, and two unanswerable/deferred-content cases.
- The [pre-answer annotation correction](annotation-correction-1.json) retained
  the first freeze: the allowed report's appendix actually contains the dataset
  total page count. The restricted question was changed to the double-annotation
  page count **before any answer call**, after original-page inspection.
- [Repair addendum](repair-1/protocol-addendum.md): same bytes, index, questions,
  gold facts, models, settings and budgets; no parser changes. Both arms replayed
  once, alternating order, concurrency one, retries zero. Model outputs are
  stochastic and caches differ; this is not a causal or variance estimate.
- The corpus was already used for parser development, so it is not held out.
  Review is by **Codex, a model**, inspecting answers, original-page facts and
  supplied/cited text, not an independent human judge or paid external judge.
- This is A versus D as a whole product. D adds assessment guidance and possible
  deterministic refusal. B/C and passive-assessor ablations remain unperformed.
  The named cross-document question was answered with first-round evidence in
  both passes; it does not establish a live source-bound dependency binding gain.

## Changes and observed failures

The [retained live rankings](../../../tests/fixtures/planned_pdf_rankings.json)
show the homework, project, midterm and team-size queries originally ranking the
correct four children first. Global cross-query RRF instead selected generic
lecture passages. Representative selection now reserves each requirement's
query-local leader before filling by global rank; document round-robin and the
shared evidence budget remain in place. Guest-lecturer retrieval also recovers.

The leading `Using only "docling-report.pdf"` clause originally treated `only` as
part of the filename, causing a false missing-file response in both arms. It now
resolves that exact file without broadening scope. Assessor prompt v2 clarifies
that names already in the question stay literal in target-free reformulations,
and that quotes must be contiguous exact text, with separate references for
separated table headers/values. Validation, retry limits and error behavior were
not relaxed, and no model outputs were automatically repaired.

Remaining failures are retained:

1. **Assessor quote failure:** `apple-income-planned.json` and
   [the repaired attempt](repair-1/apple-income-planned.json) both fail. The
   second assessor output still inserts an ellipsis and literal escaped
   whitespace into a stitched table quote. Stronger instructions did not solve
   the failure. Strict provenance validation rejects it; no answer is saved.
2. **Evidence lost while packing:** `apparent-conflict` retrieves the correct
   sales row as a top candidate but excludes it from the 4,096-token context.
   Expanded PDF cell metadata is expensive; lower-ranked admitted parents leave
   insufficient space for the selected sales child. Planned mode then refuses.
   Single mode states the correct periods but cites an income table that does
   not contain those sales figures: reference correctness is 1, source support
   is 0. `apple-sales-single` also refuses after its sales evidence is excluded.
3. **Dense table corruption:** all four original Alabama values (18,870; 23,022;
   22,650; 71,137) are absent from the canonical extraction. Both single answers
   instead cite unrelated 29,905; 38,487; 102; 1,656. Repaired planned mode
   withholds the missing numbers and correctly explains that checks are not
   firearms sold. This is safer behavior, but still incomplete PDF support.
4. **Units and citation coverage:** planned sales answers cite a child containing
   values/header supplements without a units label; a different supplied income
   statement has the label. The review gives partial contextual/citation credit,
   not full support. The repaired single income answer also leaves the first
   bullet without an inline citation.
5. **Unnecessary supplementary work:** missing enrollment, forecast and screenshot
   questions consume additional rounds without finding the absent facts. Bounds
   hold, but this pass does not show an efficiency benefit.

## Quality, separately from runtime

Per-answer and expected-point judgments are in [reviewed-cases.json](reviewed-cases.json).
Correctness/completeness are macro means over 14 questions with requested facts,
including failed/blocked turns as zero. Fully unanswerable cases use separate
abstention denominators. Final evidence coverage scores only actual final answer
context, including supplements. Failed requests supply no final answer context.

| Metric | Before single | Before planned | Repair single | Repair planned |
| --- | ---: | ---: | ---: | ---: |
| Completed / intended turns | 16/16 | 9/16 | 16/16 | 15/16 |
| Request errors / blocked follow-ups | 0 / 0 | 6 / 1 | 0 / 0 | 1 / 0 |
| Requested-point correctness | 80.00% | 42.86% | 87.14% | 80.00% |
| Requested-point completeness | 80.00% | 42.86% | 87.14% | 80.00% |
| Final semantic evidence coverage | 72.86% | 41.67% | 80.00% | 78.81% |
| Factual claim-group faithfulness | 75.81% | 90.00% | 76.67% | 94.00% |
| Citation support | 75.81% | 90.00% | 78.57% | 94.00% |
| Citation coverage | 75.81% | 90.00% | 73.33% | 94.00% |
| Appropriate full abstention | 2/2 | 1/2 | 2/2 | 2/2 |
| Incorrect full abstention | 2/14 | 2/14 | 1/14 | 1/14 |

Claim-group scores exclude claim-free refusals/errors; higher faithfulness alone
therefore does not establish better overall quality. Reference correctness and
completeness coincide under this requested-point rubric; claim correctness and
citation support are separately retained. A semantically correct uncited or
unsupported assertion can receive reference credit while failing source support.

### Per-question repair changes

| Case | Planned before -> after | Remaining interpretation |
| --- | --- | --- |
| Paper facts / paraphrase | Complete -> complete | Correct source-supported requested facts |
| Lecture logistics / grades | Error -> correct answer | Query-local evidence leaders retained |
| Lecture follow-up | Blocked -> correct answer | Conversation resolves teams and timing |
| Apple sales | Correct answer -> correct answer | Units citation only partially supported |
| Apple income | Error -> error | Invalid exact-quote output persists |
| Technical table / tradeoff | Complete -> complete | Original-page values verified for this row only |
| Cross-document dataset | Complete -> complete | First-round context already sufficient |
| Dense table | Error -> supported caveat, missing numbers | Parser still loses the requested values |
| Apparent conflict | Incorrect abstention -> same | Correct candidates excluded by packing |
| Partial lecture | Error -> correct names and missing-count notice | Supplementary rounds do not discover enrollment |
| Missing forecast | Error -> correct abstention | No forecast invented |
| Restricted dependency | False missing-file notice -> correct partial answer | Scope-clause fix affects both arms |
| Screenshot | Correct abstention -> same | Visual recognition remains deferred |

### Selected-stage retrieval diagnostics

[Anchor labels](anchor-labels.json) map frozen original-page strings to canonical
spans; [diagnostics v2](retrieval-diagnostics-v2.json) retain per-query vector,
BM25, fusion and reranked stages separately from final selection. Gold anchor
labels are incomplete semantic relevance labels. Recall requires every anchor
of a fact; binary child relevance requires touching any annotated anchor.
Precision uses denominator five even when fewer results exist. MRR is cut off
at five; NDCG uses binary gain and log2 discounts. Missing anchors remain misses.

| Selected child metric, K=5 | Before single | Before planned | Repair single | Repair planned |
| --- | ---: | ---: | ---: | ---: |
| Fact-anchor Recall | .7048 | .5024 | .7762 | .7405 |
| Child Precision | .3571 | .2286 | .3714 | .3286 |
| Hit Rate | .8571 | .7143 | .9286 | .9286 |
| MRR@5 | .7857 | .6190 | .8571 | .8095 |
| NDCG@5 | .6975 | .4852 | .7690 | .6921 |

These are macro means over 14 fact-bearing turns, not a general retrieval
benchmark. `Yaoliang Yu` fails literal matching because extraction joins the
name; semantic review still credits the supplied name. The four Alabama values
are genuinely missing. Neither case is silently removed from anchor recall.

## Runtime, models and operations

Resolved runtime/source hashes are in [before](resolved-runtime.json) and
[repair](repair-1/resolved-runtime.json). GPT-4.1 resolved to
`gpt-4.1-2025-04-14`; embeddings used `text-embedding-3-small`. The existing local
configuration enabled `BAAI/bge-reranker-v2-m3` on MPS; its revision is retained.
This does not change the repository's default-disabled reranker. Evidence budget
4,096; final K=5; candidate limit 20; three rounds/six total logical queries;
request limit 180s; SDK retries zero. No `.env` edits.

| Successful SSE latency, seconds | Before single | Before planned | Repair single | Repair planned |
| --- | ---: | ---: | ---: | ---: |
| Samples | 16 | 9 | 16 | 15 |
| First answer delta: mean / P50 / P95 | 2.32 / 2.15 / 4.17 | 7.86 / 9.71 / 11.56 | 2.08 / 1.93 / 3.14 | 8.38 / 8.79 / 11.34 |
| Complete response: mean / P50 / P95 | 2.84 / 2.96 / 4.58 | 8.26 / 10.39 / 11.88 | 2.62 / 2.58 / 4.07 | 8.95 / 9.09 / 11.84 |

First delta means nonempty answer text, not a progress/source event. Completion
means HTTP stream close. Linear percentile interpolation; one sequential client.
Failed-request timing and stage distributions are separately recorded in
[measurement-v2.json](measurement-v2.json); failures are retained in reliability.
Startup is separate, per-request network/model waits are included. The 26.74s
backend test run overlapped early repaired requests and provider cache use differs;
these numbers do not support a speedup claim or load-capacity estimate.

| Actual answer-workload provider usage | Before single | Before planned | Repair single | Repair planned |
| --- | ---: | ---: | ---: | ---: |
| GPT input tokens | 50,620 | 91,383 | 55,813 | 143,821 |
| GPT output tokens | 1,139 | 7,497 | 1,307 | 10,018 |
| Cached GPT input tokens (included above) | 0 | 3,968 | 41,088 | 18,688 |
| Query embedding input tokens | 442 | 672 | 475 | 1,026 |

Usage includes downstream-invalid structured responses and question resolution,
not just final generation. Ingestion embeddings are recorded separately. Actual
billed cost is **unavailable** without a provider billing statement; local parsing
and reranking are not presented as paid API costs. Provider queue time and search/
fusion wall times are not independently instrumented and remain unavailable.

All five uploads became Ready, with original SHA-256 and byte-range checks passing.
The index contains 621 children and 154 parents, initially 30,060,353 bytes including
originals, SQLite and vectors. [Ingestion](ingestion-summary.json) and
[isolated lifecycle check](repair-1/lifecycle.json) preserve timings: deleting the
Apple PDF removes it from the library and makes its original return 404 while
saved evidence and retrieval history remain unchanged. All 56 completed exchanges
round-trip their answer and retrieval trace. No in-place update endpoint exists.
After-delete index size includes newly saved histories and is not a reclaimed-byte
measurement. No production data was touched; the evaluation server was stopped.

## Gates, checks and next work

| Frozen development gate | Outcome |
| --- | --- |
| Five Ready PDFs with correct originals/page identity | Pass |
| All 32 intended turns finish without errors | Fail: initial 25/32, repaired 31/32 |
| Zero invented cited facts across paired answers | Fail: single dense-table values; citation support gaps also remain |
| No loss of mean correctness or final coverage versus single | Fail: repaired planned .8000/.7881 versus single .8714/.8000 |
| Both unanswerable questions abstain | Pass in repaired planned mode |
| Original delivery, history, isolated delete | Pass via HTTP; no new browser run |

Offline checks: [104 scoped tests](repair-tests-3.log) and
[714 passed, 1 skipped backend suite](backend-tests-1.log). Earlier attempts remain:
missing import path, then two mistakes in new test fixtures (a wrong expected child
ID and missing fixture filename). Both fixture mistakes were corrected; no product
behavior was weakened to pass. Existing dependency deprecation warnings remain.

Metric records are append-only. The copied offline wrapper put incorrect generic
not-applicable statuses on live commands; `measurement-v2.json` explicitly supersedes
those statuses. Diagnostics v1 also read pre-rerank candidates for its per-query
reranked field; v2 corrects that field while preserving the original attempt.
Neither correction changes raw requests, model outputs, or selected-stage scores.
Source preparation timings were not captured by that wrapper and are unavailable.

Next implementation should address financial-table packing/units and replace the
assessor's fragile free-form quote selection with a reliably source-bound contract,
using these frozen failures as regressions. Dense-table extraction remains a
separate unresolved capability limit. Complete scoped implementation checks before
another acceptance run. An independent human review, held-out population, genuine
contradictions and production load/billing evidence remain outstanding. User
acceptance and feature-specific merge authorization are still required.
