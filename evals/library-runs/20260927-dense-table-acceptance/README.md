# Dense-table live acceptance: failed

At product commit `8d3403e8c16142be863f0a2e779bd9cb78d14be2` on `v2`, all six
frozen HTTP/SSE requests completed, but none answered every requested point.
Only **2 of 24 requested point instances** were correct and complete: both
background-checks-not-sales disclaimers. The fresh parser output contains the
correct table values and retrieval finds them; final evidence packing excludes
the table. This run does not pass feature acceptance.

## Answer and citation findings

| Frozen case | Single mode | Planned mode |
| --- | --- | --- |
| `dense-table` | 1/5 points. Correct disclaimer; explicitly omits four values absent from the supplied excerpt. | 1/5 points. Same supported disclaimer and four explicit omissions. |
| `state-totals` | 0/3 points. Invents three totals and cites a notes-only excerpt. | 0/3 points. Returns an insufficient-information refusal with no final sources. |
| `grouped-and-blank-cells` | 0/4 points. Malformed filename scope stops retrieval and generation. | 0/4 points. Same scope failure, surfaced as a generic missing/not-ready document message. |

The single-mode state totals are Alabama **29,801** instead of **71,137**,
Alaska **5,733** instead of **7,095**, and Arizona **32,667** instead of
**27,087**. All three bullets cite `[1]`, whose actual source contains only
footnotes and the disclaimer. Neither those invented numbers nor the correct
totals appear in the actual generation inputs. Valid citation IDs did not
establish support.

Across five substantive factual claim groups, two are supported and have
supporting citations. The other three are the wrong totals. Missing-information
statements and claim-free refusals are reviewed separately; they do not inflate
the claim denominator. Three of six original-page-answerable requests fully
refuse. The dense-table answers' context limitations are honest but incomplete.
No fully unanswerable questions were included.

The grouped/blank-cell requests never reach a model, so live interpretation of
the Rentals blanks and repeated Handgun headers remains **unexercised**. Absence
of a blank-as-zero error is not evidence of success.

Two Codex model reviewers independently scored the answers, followed by an
[explicit reconciliation](review/reconciliation.json). They agree on all 24
point scores, five claim groups, citation support, and abstention outcomes.
Their relevance interpretations differ for three refusals: primary mean 4/6,
secondary 4.5/6. Both scores remain visible; no human review or paid judge is
claimed. The main metrics retain the primary scores. See the
[primary review](review/reviewed-cases.json), [second review](root-review.json),
and [assessment/reference audit](review/assessment-reference-review.json).

## Verified failure boundaries

1. **Serialized table context exceeds the budget.** Child 0 contains the three
   annotated state rows. Its body is 501 tokens, but the complete serialized
   source is 4,673 tokens against a 4,096-token evidence budget. Its 221 cell
   tuples alone consume 4,024 tokens. Parent expansion also exceeds the budget,
   and the current packing path cannot keep the child even by itself. The three
   actual generation calls receive the same 305-token notes-only context,
   canonical offsets `4907:5738`, with no table cells. The relevant table child
   is selected by retrieval and excluded from packing in all four requests that
   execute retrieval. See [offline diagnostics](diagnostics/findings.json),
   [serialized child context](diagnostics/child-0-context.txt), and
   [actual generation-input audit](diagnostics/generation-input-audit.json).
2. **A qualifier after a quoted filename becomes part of its reference.**
   `In "background-checks.pdf" for November 2015, ...` produces the unresolved
   reference `background-checks.pdf" for November 2015`. The PDF is ready and
   the request supplies its valid file ID, but textual scope resolution still
   rejects it. Both modes execute zero retrieval queries and zero provider
   calls for this question. Planned mode discards the initial scope error and
   resolves again against an empty catalog, producing its generic message.
   See [scope reproduction](diagnostics/scope-reproduction.json) and the
   [planned follow-up](diagnostics/scope-plan-followup.json).

The next implementation should make the table evidence fit while preserving
row, parent/leaf header, blank-cell, and page associations, and correct the quoted
filename boundary. Validate those changes with scoped offline regressions before
repeating the frozen six-request workload in a new run directory. These blockers
precede the remaining technical-table repair. This run changes no production code
and does not establish that either proposed fix works.

## Retrieval and measurement definitions

The complete [20-metric inventory](metrics/measurement.json) separates each arm,
the combined workload, and shared preparation. [Frozen fact labels](metrics/fact-labels.json)
bind original source rows and full header paths to the fresh extraction before
ranking/answer review. [Stage diagnostics](metrics/retrieval-diagnostics-2.json)
retain vector, lexical, fusion, reranking, selected-child, and supplied-evidence
results, including exclusions.

K is 5. Recall uses source-bound facts; Precision, Hit Rate, MRR and NDCG use
binary relevant child labels over this single-file, ten-child corpus. These are
different evaluation units. Final selected-child Recall, Hit Rate, MRR and NDCG
are each 1 for the four requests that execute retrieval, and 0 for the two scope
rejections; their six-request means are 0.666667. Precision is 0.4 for each
dense-table request, 0.2 for each state-totals request, and 0 for scope rejections,
giving mean 0.2. Per-query stage means exclude unexecuted scope-rejected queries.

Final supplied-evidence coverage, correctness and completeness each have a
question-macro mean of 0.066667 and a point-micro mean of 2/24 = 0.083333.
Structural evidence coverage agrees with the semantic review. Candidate retrieval
success therefore does not imply that the answer receives the evidence.

## Timing and usage

Times are measured from request start to the first nonempty answer delta and
HTTP stream closure, respectively. All requests run sequentially, concurrency 1.

| Case / mode | First delta (s) | Complete (s) | Response path |
| --- | ---: | ---: | --- |
| dense-table / single | 2.468035 | 3.272476 | Provider-generated |
| dense-table / planned | 11.416895 | 12.439272 | Provider-generated |
| state-totals / single | 1.309715 | 1.643842 | Provider-generated |
| state-totals / planned | 3.975200 | 3.980017 | Programmatic refusal after retrieval |
| grouped-and-blank-cells / single | 0.002975 | 0.004347 | Scope rejection |
| grouped-and-blank-cells / planned | 0.003483 | 0.004778 | Scope rejection |

For the three provider-generated answers, first-delta mean/P50/P95 are
5.064882/2.468035/10.522009 seconds; complete-response mean/P50/P95 are
5.785197/3.272476/11.522592 seconds. Percentiles use linear interpolation.
The mixed six-response completion mean is 3.557455 seconds, but includes two
near-immediate scope rejections and one programmatic refusal; it is not a normal
answer-generation performance estimate. The sequential workload spans 21.495778
seconds, or 0.279125 completed requests/s. No load-capacity claim is made.

The answer workload uses seven `gpt-4.1-2025-04-14` calls: two planners, two
assessments and three generation streams. Actual usage is 9,502 input tokens
(including 1,280 cached input tokens) and 1,192 output tokens. Eleven query
embedding calls use 244 tokens. Preparation adds one embedding call with 3,414
tokens, giving 19 SDK calls overall. Actual billing and local compute cost are
unavailable. Recorded zero errors, timeouts and retries describe transport and
provider execution, not semantic correctness.

Upload-to-ready takes 15.287080 seconds for one page, ten children and five
parents; parse time is 13.831536 seconds. The recorded post-upload index size is
1,731,080 bytes; after answers and server shutdown it is 3,107,336 bytes. Startup
to server readiness is recorded separately at 6.083 seconds, including the
4.283675-second application construction measured inside that interval.
Endpoint timing includes network and
provider waits; model initialization can affect startup/first parse/first query.
There is no update/delete or concurrency-above-one measurement in this scope.

## Reproduction, records and limits

- [Frozen protocol](protocol.md) and [cases](frozen-cases.json): three questions,
  two modes, one pass, no paid reruns. All original questions are answerable.
- [Preparation](preparation.json) and [resolved runtime](resolved-runtime.json):
  unchanged original PDF SHA-256
  `4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407`,
  GPT-4.1, `text-embedding-3-small`, hybrid K=5, BGE reranking on MPS, evidence
  budget 4,096, planned limits of three rounds/six queries. The BGE revision is
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. Provider timeout is 180 seconds,
  retries zero, client timeout 240 seconds. Other resolved settings are retained.
- [Fresh index snapshot](index-snapshot.json), [ingestion](ingestion.json),
  [SDK/stage observations](server-observations.jsonl), and six case/mode JSON
  files retain exact requests, answers, events, rankings, source geometry,
  exclusions, selected references and saved history. The isolated data directory
  is `data/evals/20260927-dense-table-acceptance/` (ignored by Git).
- Answer and retrieval-history equality pass for all six. Three raw source
  equality flags remain false because saved sources add `file_deleted: false`.
  All shared source fields match; this schema difference is documented rather
  than overwriting the original flags or reporting a storage failure.
- Both actual assessments select the disclaimer reference `p4`, offsets
  `5449:5738`, and preserve it faithfully; no table supplements are attached.
  State-totals planned uses an empty-context application assessment. The scope
  failures perform no assessment. These observations do not test live blank-cell
  grounding or the original-page viewer interaction.
- The historical `dense-table` question remains at 1/5 points in both modes.
  Its old single answer invented four values; this run's single answer omits
  them honestly. New state-totals single still invents three values. The later
  product version, intervening retrieval/citation changes and fresh single-file
  corpus prevent a causal parser-only comparison. The two new questions have no
  historical live baseline. Three development rows are not a held-out benchmark.
- Failed [preparation attempt 1](prepare-1.log) lacked the project import path;
  [preparation attempt 2](prepare-2.json) passed. Failed
  [measurement attempt 1](metrics/measurement-1.log) had a syntax error before
  execution; [attempt 2](metrics/measurement-2.json) passed. The initial retrieval
  analysis counted a scope rejection as an executed empty query;
  [the corrected analysis](metrics/retrieval-diagnostics-2.json) excludes it from
  per-query means while retaining its failed final outcome. All earlier artifacts
  remain. None of these evaluator corrections caused another provider call.
- [Shutdown](server-stop.json) confirms the test service stopped, port closed and
  ownership lock released. Production files and `.env` remain unchanged; the
  existing user library was not used. [Final verification](verification-1.json)
  records artifact consistency, content/link/format review and frozen-input checks.
- The [initial staged whitespace check](format-review-1.json) flags intentional
  trailing tabs in two exact serialized table contexts (blank header positions).
  The raw contexts and failure log are preserved byte for byte. The
  [scoped format review](format-review-2.json) checks all other staged files and
  documentation links, explicitly excluding only those two raw files and that log.

Passing record checks or transport checks does not override the failed answer
acceptance or authorize a merge into `main`.
