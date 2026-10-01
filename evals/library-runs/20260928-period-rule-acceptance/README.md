# Period/rule matched acceptance: improved answers, one gate still fails

All four component requests complete. Three pass all case gates, up from two in
the [baseline](../20260928-answer-rules-acceptance/README.md). The wrong-year values
are now withheld and the invented rule no longer appears in the factual-condition
case. Acceptance still fails because the missing-year plan adds a duplicate
evidence-availability requirement and retains an inaccurate column qualifier.
No request was retried, repaired or rerun.

## Matched results

| Case | Before | Current result | Current gate |
| --- | --- | --- | --- |
| Original rule | 4/4 points, pass | 4/4 points; same four facts and actual user rule | Pass |
| Paraphrased rule | 4/4 points, pass | 4/4 points; values/blanks and citations preserved | Pass |
| Factual condition | 3/3 points; invented rule | 3/3 points; no rule invented; missing explanation retained | Pass |
| Missing year | 0/2 points; 2015 values stated as 2016 | 2/2 missing-value points; correct refusal, but planning/wording defects remain | Fail |

[Review](review.json) records all exact answer statements, expected points,
semantic judgments and per-case comparisons. Point delivery improves from 11/13 to
13/13. This point score measures the requested facts or missing-value disclosures;
it does not waive the plan-scope or wording defects described below.

Supported, individually cited factual groups improve from 10/12 to 12/12. The
current groups comprise ten cell-value/blank observations and two correct source
period observations embedded in the missing-value statements. All three absence
statements are also reviewed separately: one missing explanation and two missing
2016 values. The Pre-Pawn qualifier defect is explicitly retained in that review,
rather than being treated as a supplied count or concealed by the support score.

Appropriate refusal on the wholly unanswerable case improves from 0/1 to 1/1.
Incorrect full refusal on the two fully answerable cases stays 0/2, and the correct
partial limitation stays 1/1. This is a generated refusal of both requested
values, not the application's local all-missing response. All four cases still
make a generation call.

## Remaining failure

[missing-year.json](missing-year.json) now marks both requested November 2016
values missing and explicitly explains that only November 2015 evidence exists.
No 2015 number is relabeled as 2016. However, the plan contains an extra R3:
"Whether the supplied excerpts establish these values for November 2016."
This repeats the conditional answering instruction's evidence check rather than
adding a separately requested source fact. The assessor marks R3 supported by
period passage p2, preventing the all-missing generation bypass. The exact-copy
rule check establishes text provenance but does not prevent this duplicate
classification. Rule provenance passes 4/4; full rule/fact separation passes 3/4.
The baseline also had 3/4 separation, but its failed case was the factual condition;
this aggregate alone would hide that per-case regression.

The same plan and answer still label Pre-Pawn Handgun as "ungrouped Pre-Pawn
Handgun". The user's ungrouped qualifier applies only to the first Handgun column.
This defect already existed in the baseline and survives the v5 instruction.
Correctly withholding unavailable values does not make that qualifier correct.

Next work should address these observed planner responsibilities: keep conditions
about evidence sufficiency in answering rules, and preserve each requested
column's own qualifiers without transferring them to adjacent columns. Full
retrieval/supplementary-search acceptance has not been performed or authorized by
this result. Do not infer a general semantic validator from one successful year
contrast or add a silent output-repair step.

## Evidence and performance

The question file, component runner and frozen evidence are byte-identical to the
baseline. Safe runtime settings match. Available source-fact coverage stays 10/10
occurrences across three cases; absent explanation/2016 facts have no gold evidence
and are excluded rather than called zero-recall cases. The actual assessor and
generator contexts remain identical at 2,604 local cl100k_base tokens. Exact
passage and attached-header offsets match the original extraction in every case.
Supported value assessments still select the row passage alone; the application
attaches period/header passages. Do not claim the model independently selected
those headers merely because they appear in the normalized record.

Product commit: `4997e75`. Resolved model: `gpt-4.1-2025-04-14`, unchanged from the
baseline. Twelve provider calls complete with zero errors, timeouts or retries.
Usage is 39,280 input plus 2,397 output tokens (41,677 total), versus 40,242 total
baseline tokens. Billed cost is unavailable without a billing statement.

| Nonstreaming component timing, seconds (n=4) | Mean | P50 | P95 |
| --- | --- | --- | --- |
| Planning | 4.164 | 3.822 | 5.589 |
| Assessment | 3.650 | 3.695 | 4.514 |
| Generation | 2.025 | 1.875 | 2.843 |
| Component sequence total | 9.846 | 10.083 | 11.519 |

The baseline component mean is 9.351 seconds; this small sequential sample does
not establish a performance change. Percentiles use linear interpolation. Provider
queue time is included but not isolated; no local model loads. These are component
timings, not HTTP response or first-answer-delta latency. Retrieval/reranking,
supplementary searches, indexing, saved-history parity and serving throughput are
not exercised. [All 20 metrics](measurement.json) retain their values or explicit
not-applicable/unavailable status, source checks and per-case comparisons.

## Records and limits

[Protocol](protocol.md) was frozen before requests; the
[original protocol](frozen-original-protocol.md) remains verbatim.
[Preparation](preparation.json) retains device, safe configuration and hashes.
[Provider events](provider-events.jsonl) contain every exact SDK input/output,
resolved revision, duration and usage. [Frozen evidence](frozen-evidence.json)
retains source identity, original retrieval metadata and context; no new retrieval
was run. Current assessment has empty executed-query metadata and the same
final-round boundary as the baseline. No product code changed during evaluation.

[Artifact review](artifact-review-1.json) verifies hashes, event accounting, metric
completeness, English content, links and formatting. One Codex /root reviewer
performed semantic review; there is no independent second or human review. These
are four development questions, one attempt each. Multiple prompt/validation
changes and model variability limit causal attribution; no statistical stability,
held-out generalization, end-to-end acceptance or merge approval is established.
