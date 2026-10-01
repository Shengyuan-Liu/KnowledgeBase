# Dependency acceptance: answers recover, one classification gate still fails

All four component requests complete and deliver all 13 expected answer points.
Three of four case gates pass. Conditional retrieval and column scope recover in
this sample, but the factual-condition planner now duplicates the factual question
into `answer_rules`. Correct answers do not override that classification failure.
No case was repaired or rerun; product code remained frozen at `bb4bc94`.

## Matched comparison

| Case | Immediate baseline | Current result | Current gate |
| --- | --- | --- | --- |
| Original rule | 4/4 points, pass | Four correct cells, separately quoted user rule, individual citations | Pass |
| Paraphrased rule | 4/4 points, pass | Same four correct values/blanks and citations | Pass |
| Factual condition | Invalid dependent plan; no answer | Three independent queries and 3/3 points; factual condition wrongly copied into answer_rules | Fail |
| Missing year | Correct refusal, wrong Pre-Pawn qualifier | Correct column paths, two missing values, local refusal | Pass |

The [immediate baseline](../20260928-planner-fact-scope-acceptance/README.md)
completed 3/4 requests, passed 2/4 gates and delivered 10/13 intended points. Its
completed-only semantic scores were 10/10, with three unavailable points from the
failed request. This run completes 4/4, passes 3/4 gates and scores 13/13, with no
unavailable answer points. The improvement is recovered point delivery; both
completed-only answer fractions are 100%. Rule classification regresses from
4/4 to 3/4 even though the overall case-gate count improves.

[Semantic review](review.json) retains every expected-point judgment, positive
factual claim, absence statement and classification decision. Ten positive
factual groups are supported and individually cited (10/10), compared with 8/8
in the baseline whose conditional answer was absent. This denominator change
is not a faithfulness improvement. The wholly unanswerable case appropriately
refuses (1/1), the two fully answerable cases avoid incorrect refusal (0/2), and
the partially answerable case correctly discloses its missing explanation (1/1).

## Recovered behavior and remaining failure

In [factual-condition.json](factual-condition.json), the planner now emits three
initial queries with route `decomposed` and no dependencies. They retain the known
row/document/period and request the blank cell, Handgun value and explanation.
The assessor supports the two available facts, marks the explanation missing and
the answer reports all three points correctly. The final-round harness stops at
`round_limit`; it does not exercise supplementary retrieval.

However, the planner also returns this `answer_rules` item:

> if Alabama's Rentals Handgun cell is blank, what is Alabama's ungrouped Handgun value, and does the document explain why that Rentals Handgun cell is blank

This is an exact substring of the question, so existing text-provenance validation
passes. Under the unchanged rubric it is a factual conditional question, not a
separate answering instruction. The expected list is empty. All three facts
remain in requirements, so this is semantic duplication rather than lost answer
coverage or invented text. The new observation is retained as a failed gate and
has not been patched during this evaluation.

In [missing-year.json](missing-year.json), R1 names "ungrouped Handgun" and R2
names "Pre-Pawn Handgun"; Q2 and the assessment likewise retain the correct
Pre-Pawn name. Both requirements keep November 2016, while the evidence only
contains November 2015. Both are missing with no references, so generation is
bypassed and the local insufficient-evidence response is returned. Its generic
wording names neither the year nor individual fields, as disclosed in the frozen
rubric. There is no extra availability requirement or false 2016 value.

All four planner calls accept the changed schema. All resulting plans are
independent; this run does not test a live genuine source-derived dependency.
The joint prompt/schema change and one observation per question do not isolate
which instruction caused an improvement or the remaining regression.

## Evidence and measurements

Resolved model: `gpt-4.1-2025-04-14`, unchanged. The [preflight](preflight-1.json)
verifies identical questions, case order, runner, frozen evidence and safe runtime
settings against the immediate baseline. All executed assessments and generations
see the same 2,604-token context, with source/header offsets checked against the
original extraction. All ten available source-fact occurrences reach the context
and are fully covered. The baseline's other two occurrences never reached
assessment because planning failed; this recovery is not a packing change.
Unavailable 2016 values and explanation have no gold evidence and receive no
invented zero-recall score.

Eleven provider calls complete (four planning, four assessment, three generation),
with zero application errors, provider errors, timeouts or retries. Usage is
37,117 input and 2,232 output tokens, 39,349 total, versus 29,129 in the baseline.
The increase includes the recovered assessment/generation calls and changed
planner input; it is not a like-for-like per-request cost comparison. Billed cost
remains unavailable without billing evidence.

| Nonstreaming timing (seconds) | n | Mean | P50 | P95 |
| --- | --- | --- | --- | --- |
| Planning | 4 | 3.172 | 2.675 | 4.892 |
| Assessment | 4 | 2.064 | 1.925 | 2.634 |
| Generation or local refusal | 4 | 1.204 | 1.364 | 2.004 |
| Complete component sequence | 4 | 6.445 | 5.958 | 9.464 |

Baseline component mean/P50/P95 were 8.057/8.882/9.220 seconds, including its
failed request. Generation/refusal now includes three model calls and one local
bypass. These small, differently completed samples do not demonstrate a stable
speed improvement. Percentiles use linear interpolation; provider queue time is
included but not isolated, concurrency is one and no local model loads. These
are component durations, not HTTP or streaming first-answer-delta measurements.
[All 20 metrics](measurement.json) retain measurements or explicit scope reasons.
Retrieval ranking, indexing, supplementary searches, history and serving
throughput are not exercised.

## Records and limits

- [Protocol](protocol.md), [original rubric](frozen-original-protocol.md) and
  [baseline protocol](baseline-protocol.md) were preserved before paid calls.
- [Preparation](prepare-1.json), [safe settings and hashes](preparation.json),
  [frozen questions](cases.json) and [frozen evidence](frozen-evidence.json).
- [Raw SDK requests/responses](provider-events.jsonl), [run output](live-1.log),
  exact plans/assessments/answers in the four case files, and [review record](review-1.json).
- [Measurement command](analysis-1.json) and [artifact/documentation review](artifact-review-1.json).

Reviewer: one Codex /root semantic review, not an independent human review. Cases
are reused development regressions and their wording now appears in prompt
examples. This result does not establish held-out generalization, repeatability
or full API/multi-round acceptance. The next implementation issue is distinguishing
factual conditional clauses from actual answering instructions while preserving
all requested facts. This evaluation adds no product repair and authorizes no merge.
