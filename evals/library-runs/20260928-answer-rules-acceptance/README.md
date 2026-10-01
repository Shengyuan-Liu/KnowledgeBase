# Answer-rule live acceptance: failed

The four-case fixed-evidence run completes, but only two cases pass all frozen
gates. The original conditional-rule defect does not recur on its exact question
or a paraphrase. Two controls fail: the planner invents an answering rule, and the
assessor plus generator use November 2015 figures to answer a November 2016 question.
All raw outputs are preserved; no case was repaired or rerun.

## Results

| Case | Classification and assessment | Answer points | Gate |
| --- | --- | --- | --- |
| Original rule | Four facts supported; actual user rule separated | 4/4 | Pass |
| Paraphrased rule | Four facts supported; actual user rule separated | 4/4 | Pass |
| Factual condition | Three factual requirements preserved, explanation correctly missing; an unrequested rule invented | 3/3 | Fail |
| Missing year | User rule separated, but both unavailable 2016 facts incorrectly supported | 0/2 | Fail |

[Semantic review](review.json) scores 11/13 expected answer points. Of 12 factual
sentence/list-item groups, 10 are supported and have supporting inline citations;
the two wrong-year claims are unsupported despite valid citation IDs. The separate
missing-explanation statement is correct. The wholly unanswerable case has 0/1
appropriate abstentions. Fully answerable cases have 0/2 incorrect abstentions;
the partially answerable case gives the correct limitation (1/1).

Available source-fact coverage is 10/10 occurrences across three cases, using the
original source-bound cell/header/row labels. Unavailable explanation and 2016 facts
have no gold evidence and are excluded from this denominator, not silently scored
as retrieved facts. All four cases receive the exact same 2,604-token context.
Exact quote/offset checks pass for every assessor reference and attached header.
Those structural checks do not validate the assessor's semantic conclusions.

## Failure evidence and next work

In [factual-condition.json](factual-condition.json), the user asks an actual
conditional fact question and provides no answering instruction. The planner
still returns: "If the excerpts do not establish a requested cell's contents,
state that limitation." The three factual requirements survive and the answer is
correct, but the invented rule violates the no-invention contract. Its wording
resembles the planner prompt's example; that resemblance is an observation, not a
verified causal explanation.

In [missing-year.json](missing-year.json), both requirements explicitly request
November 2016, but the assessor marks them supported using Alabama row passage
`p5`. Attached period passage `p2` says `November - 2015`. The final answer asserts
2016 values of 23,022 and 14, both copied from the 2015 table. It never discloses
the missing year. The plan additionally calls Pre-Pawn Handgun "ungrouped", an
unrequested and inaccurate qualifier. Source identity, requested period and full
column path need semantic verification together; matching an entity and number is
insufficient. Valid references and explicit header attachment did not prevent this.

Next priority: reproduce the period mismatch offline and enforce the requirement
that evidence establish the requested period before claiming support; preserve
the original column qualification. Separately prevent prompt examples from becoming
invented user rules. These are observed failures, not implemented repairs. Do not
infer that a blanket year regex or an automatic answer rewrite would solve them.

## Performance and scope

Product version: `5447c29`; resolved model: `gpt-4.1-2025-04-14`. All 12 provider
calls complete with zero errors, timeouts or retries. Provider usage is 37,916
input and 2,326 output tokens (40,242 total); billed cost is unavailable.

| Component timing (seconds, n=4) | Mean | P50 | P95 |
| --- | --- | --- | --- |
| Planning | 4.889 | 4.732 | 6.772 |
| Assessment | 2.800 | 2.678 | 3.464 |
| Generation | 1.656 | 1.637 | 2.088 |
| Total component sequence | 9.351 | 9.007 | 11.294 |

Percentiles use linear interpolation. Concurrency is one; SDK stage durations
include provider queue time without isolating it, and no local model is loaded.
These are nonstreaming component durations, not HTTP complete-response latency or
first-answer-delta latency. Retrieval ranking, multi-round supplementary search,
ingestion, index lifecycle, saved-history parity and serving throughput are not
exercised. [Measurement inventory](measurement.json) retains all 20 metrics and
their scope/status, exact observations and coverage bindings.

The [protocol](protocol.md) and [cases](cases.json) were frozen before calls.
[Preparation](preparation.json) retains device, safe settings, code and input
hashes. [Provider events](provider-events.jsonl) retain all exact SDK inputs,
outputs, usage and resolved revisions. [Frozen evidence](frozen-evidence.json)
preserves the historical context and its original retrieval trace; that trace is
not a claim that retrieval ran again. Current component assessments use no executed
query metadata and a final-round boundary to prevent supplementary retrieval.

The exact original question's historical answer was already 4/4; this run improves
its classification from five requirements including a false missing rule to four
supported factual requirements plus the separate rule. The context is identical,
but the historical run was end-to-end with first-round assessment and executed
queries. Metadata and generative variation limit causal attribution. Three new
controls have no historical baseline. One attempt per question and one Codex /root
reviewer do not establish statistical stability or general v2 quality; there is no
independent second or human review. Acceptance fails and no merge is authorized.

[Offline artifact review](artifact-review-1.json) checks content, local links,
formatting, frozen hashes, measurement completeness and provider event accounting.
No product code changed during this evaluation.
