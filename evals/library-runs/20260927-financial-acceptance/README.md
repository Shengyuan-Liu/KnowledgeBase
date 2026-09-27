# Financial PDF repair: six live requests, one citation coverage failure

The targeted live pass at product commit `8f24ba3` completed **6/6 requests**.
Codex review found all **16 requested financial points** correct, complete and
supported by the supplied evidence. The former income quote-validation error and
two incorrect refusals did not recur. **Scoped acceptance still fails:** the first
bullet of the planned income answer has no inline citation. Final citation coverage
is **13/14 factual claim groups**, not full coverage. This is not overall v2
acceptance and does not authorize merging into `main`.

## Frozen scope and comparison

The [protocol](protocol.md) and [three questions](frozen-cases.json) were frozen
before calls. The comparison uses the same question text, original PDF, file scope
and expected facts as the six corresponding requests in the previous
[repair pass](../20260927-v2-pdf-live/repair-1/protocol-addendum.md). One sequential
pass alternated mode order, with zero retries, no paid judge and no code/prompt
tuning between requests. No additional answer attempts were run.

The old isolated index had deleted Apple during its lifecycle check. A new ignored
copy restored the original Apple extraction, 17 children, parent records, file ID,
revision and PDF bytes. All five documents, 621 children and parent records match
the original snapshot. Only the 17 Apple embeddings were regenerated with the same
embedding model. Their original bytes were unavailable; [preparation.json](preparation.json)
records the new vector artifact/hash and this comparison limitation. No parsing or
rechunking occurred. Production data and `.env` were not changed.

Resolved settings match the earlier repaired pass except the isolated data path:
GPT-4.1 resolved to `gpt-4.1-2025-04-14`, embeddings used
`text-embedding-3-small`, and BGE ran on MPS at the same recorded revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. K=5, candidate limit 20,
evidence budget 4,096, planner input cap 8,192 and three-round/six-query limits
were unchanged. See [resolved-runtime.json](resolved-runtime.json) for source
hashes, package versions, settings and device. The retained baseline runtime's
commit predates its uncommitted repair; its source hashes identify that repair.

Live plans, regenerated embeddings and provider/cache conditions are not guaranteed
identical. Five of six final top-five candidate lists match the baseline; planned
period-comparison selection differs. Do not attribute every changed answer or
timing solely to passage IDs. This is a small, previously seen development subset,
not a held-out population or variance estimate.

## Per-answer review

Reviewers are Codex agents, not independent humans. The original page-1 figures,
the actual supplied source text and supplements, and every answer were inspected
using the existing 0 / 0.5 / 1 requested-point and paragraph/bullet claim rubric.
The [claim and point records](reviewed-cases.json) preserve exact claims, citation
IDs, source offsets, periods, units and review notes. Original baseline scores are
retained; one old shared sales note is clarified separately, not silently replaced.

| Question / mode | Previous repaired pass | Current pass |
| --- | --- | --- |
| Sales / single | Incorrect refusal after sales evidence was excluded | Both sales amounts, periods and units correct, with supporting citations |
| Sales / planned | Correct values; cited table lacked applicable units | Correct values and same-table units, with supporting citations |
| Income / single | Correct amounts; first separate bullet uncited | Correct supported paragraph with a citation covering both amounts |
| Income / planned | Invalid copied quote caused a request error | Request completes with correct amounts; first bullet still uncited |
| Period comparison / single | Correct periods but wrong income passage cited | Sales row and headers support the period distinction |
| Period comparison / planned | Incorrect refusal | Correct supported quarter-versus-year explanation |

Amounts in millions are sales **94,930 / 391,035** and net income
**14,736 / 93,736**, for three/twelve months ended September 28, 2024. The income
request's real assessor output selects separate period, date, value and unit
passages; the application restores their exact source text. Every new assessor
reference passes the unchanged strict current-catalog provenance checks.

Valid references do not prove complete semantic support. The separate
[assessment-reference audit](assessment-reference-review.json) records that the
sales assessor selected its value row and units but omitted the period/date
passages. Those headers are present in its full context and in the source cited
by the final answer. This is an incomplete internal reference bundle, distinct
from wrong final financial facts or missing supplied evidence. The income bundle
includes all four components; the comparison bundle includes period/date headers
and redundant copies of its sales row.

The scoped gates are therefore:

| Gate | Result |
| --- | --- |
| Six requests complete without provider/schema/controller errors | Pass, 6/6 |
| Requested financial points correct and complete | Pass under the recorded model review, 16/16 |
| Final supplied evidence covers requested points | Pass under semantic review, 16/16 |
| All factual claim groups have supporting inline citations | **Fail, 13/14** |
| Zero incorrect full refusals or fabricated cited facts | Pass in this subset |
| Streamed, completed and saved answer/retrieval agree | Pass, 6/6 |

The single income answer is one cited paragraph, while planned income has two
separate bullets. The frozen rule does not let the second bullet's citation cover
the first. Repeated introductory framing in the comparison answer is retained but
excluded consistently with the earlier rubric; fiscal-quarter/year wording is
documented as an inference from the reporting periods.

## Quality and retrieval measurements

The complete 20-metric inventory is in [measurement.json](measurement.json),
separately for both modes and their combined subset, before and after. Requested
point metrics use per-question means, including errors/refusals as zero.
Claim-group metrics exclude claim-free errors/refusals; citation support scores
only actually cited groups, while coverage also counts the uncited group.

| Metric | Earlier repaired subset | Current subset |
| --- | ---: | ---: |
| Completed requests | 5/6 | 6/6 |
| Requested-point correctness / completeness | 0.5000 / 0.5000 | 1.0000 / 1.0000 |
| Semantic supplied-evidence coverage | 0.3056 | 1.0000 |
| Claim-group faithfulness | 0.4375 | 1.0000, 14 groups |
| Support of cited claim groups | 0.4167 | 1.0000, 13 cited groups |
| Inline citation coverage | 0.3125 | 0.9286, 13/14 groups |
| Incorrect full abstention | 2/6 | 0/6 |

There are no unanswerable questions in this authorized subset, so appropriate
abstention on unanswerable cases is not applicable, not zero. Broader abstention,
contradiction handling, dense-table fidelity and general model quality are not
established by these results.

[Retrieval diagnostics](retrieval-diagnostics.json) retain vector, BM25, fusion,
reranking and final selected candidates separately, plus budget exclusions and
final body/supplement spans. Aggregate selected-child diagnostics remain unchanged:
fact-anchor Recall@5 0.777778, child Precision@5 0.333333, Hit Rate@5 1,
MRR@5 1 and binary NDCG@5 0.777174. These use incomplete original-page anchor
labels, not exhaustive semantic relevance. Current literal final anchor coverage
is complete for these six cases. Earlier income evidence on page 4 could be
semantically valid while missing the page-1 literal anchors; the semantic coverage
review remains separate.

## Runtime and provider usage

| Current successful SSE requests | Single, n=3 | Planned, n=3 |
| --- | ---: | ---: |
| First answer delta: mean / P50 / P95, seconds | 2.482 / 2.427 / 2.836 | 6.980 / 7.027 / 9.428 |
| Complete response: mean / P50 / P95, seconds | 3.736 / 3.426 / 5.144 | 7.611 / 7.664 / 10.204 |

Overall mean first delta is 4.731 seconds and mean complete response is 5.673
seconds. Start is the client request; first delta means nonempty answer text, and
completion means HTTP stream close. Per-request provider/network waits are included.
Startup/local model loading took 3.643 seconds and is separate; weights were
loaded from the local cache with `HF_HUB_OFFLINE=1`, with no live warmup query.
Percentiles use linear interpolation. Stage timings are retained separately;
search/fusion and provider queue time are not individually instrumented.

| Actual usage for six answer requests | Amount |
| --- | ---: |
| GPT-4.1 calls | 12 |
| GPT input / output tokens | 37,824 / 1,606 |
| Reported cached GPT input tokens | 0 |
| Query embedding calls / input tokens | 9 / 320 |
| Separate index restoration embedding calls / input tokens | 1 / 2,545 |

Actual billed cost is unavailable without billing records. Local reranking and
index copying have no measured monetary cost. The six-request command took
34.212 seconds, sequential concurrency one; its 0.1754 requests/second does not
establish load capacity. Historical measurements used different cache conditions
and overlapped backend tests. A single pass does not support a speedup claim.

## Verification and remaining work

All raw requests, model responses, terminal usage, SSE events and per-case timing
remain in the six case JSON files and [server-observations.jsonl](server-observations.jsonl).
The [answer command](answers-1.json), [preparation](prepare-1.json),
[retrieval analysis](retrieval-analysis-1.json) and [measurement aggregation](measurement-1.json)
retain commands, code/file hashes, durations and outputs. The raw live command
records intentionally defer metric applicability to the consolidated measurement
file, including its separate index-restoration inventory. No paid judge or extra
live retry was used. The temporary server was stopped after the six requests.

Next work should address the observed final-answer inline-citation gap and keep
the sales assessor's incomplete period/date reference selection visible. Dense
table extraction omissions remain a separate unresolved limitation. Broader v2
acceptance, held-out review and user acceptance are still outstanding. No merge
is part of this run.
