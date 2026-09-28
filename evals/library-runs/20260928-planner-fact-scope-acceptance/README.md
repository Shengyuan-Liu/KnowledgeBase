# Planner fact-scope acceptance: failed with a request regression

Three of four component requests complete; only two pass all case gates. The
missing-year plan removes its duplicate evidence-availability requirement, but
still transfers "ungrouped" to Pre-Pawn Handgun. The factual-condition case now
fails planner validation and produces no answer. No case was repaired or rerun.

## Matched comparison

| Case | Immediate baseline | Current result | Current gate |
| --- | --- | --- | --- |
| Original rule | 4/4 points, pass | Same four correct values/blanks with inline citations | Pass |
| Paraphrased rule | 4/4 points, pass | Same four correct values/blanks with inline citations | Pass |
| Factual condition | 3/3 points, pass | Invalid dependent plan; no assessment or answer | Fail |
| Missing year | 2/2 missing-value points; planning defects | Two missing facts and local refusal; duplicate removed, wrong qualifier remains | Fail |

The [baseline](../20260928-period-rule-acceptance/README.md) completes 4/4, passes
3/4 gates and delivers 13/13 intended points. This run completes 3/4, passes 2/4
gates and delivers 10/13 intended points. Completed answers score 10/10; the three
failed-case semantic scores are **unavailable**, not zero-quality answers. Their
three undelivered points remain in the all-intended denominator. An error is not
an appropriate refusal.

[Semantic review](review.json) retains exact expected-point evidence, claim groups,
absence statements and per-case improvements/regressions. Eight positive factual
groups are supported and individually cited (8/8), down from twelve groups in the
baseline because one case fails and another uses a claim-free local refusal.
This denominator change is not a faithfulness improvement. Both fully answerable
cases avoid incorrect refusal (0/2); the wholly unanswerable case appropriately
refuses (1/1). The partial-limitation quality metric is unavailable because its
case fails before answering; no partial limitation is delivered.

## Confirmed failure and remaining defect

The raw [factual-condition output](failure-replay.json) retains three factual
requirements and no answering rule, but chooses `dependent`. Q2 and Q3 depend on
Q1 although their entity, document and search terms are already named in the
question. Both templates omit the required `{target}` placeholder. The application
rejects them with two `DependentQuery` validation errors. The provider returned
`completed`; schema-shaped output did not establish executable plan validity.

[Offline failure replay](failure-replay-1.json) reproduces those exact errors
without another provider call. A preliminary diagnostic note misread JSON display
escaping as literal filename characters; the append-only
[correction](failure-replay-correction.json) verifies ordinary decoded quotes.
There is no observed filename-escaping defect. The original note remains visible.

In [missing-year.json](missing-year.json), only two value requirements remain, and
both are correctly missing because the evidence is November 2015. This reaches
the existing local response: "There is not enough information in the provided
sources to answer this question." It names neither the year nor individual fields;
the predeclared rubric accepts refusal of the whole unanswerable question. There
is no generation call or invented citation. However, R2 and Q2 still incorrectly
say "ungrouped Pre-Pawn Handgun", so the case gate remains failed.

All four raw model decisions separate user answering instructions from requested
facts in this sample. That narrow classification observation does not override
invalid dependency structure or a changed column scope. Next work should clarify
logical conditions versus retrieval dependencies and keep the dependency contract
consistent with planner output, while addressing the persistent column qualifier.
This evaluation does not implement those changes or broaden to full-loop acceptance.

## Evidence and measurements

Product version: `29f805d`. Resolved model: `gpt-4.1-2025-04-14`, unchanged. Questions,
case order, runner, source evidence and safe settings match the immediate baseline.
Every executed assessor and generator sees the same 2,604-token context. Exact
reference and attached-header offsets match the original extraction.

Eight of ten intended available source-fact occurrences reach assessment/answer
contexts; all eight in exercised contexts are fully covered. The other two belong
to the failed condition case, which never reaches assessment. This is request
non-delivery, not a packing regression. There is no gold evidence for unavailable
2016 values or the missing explanation, so no zero-recall score is invented for
those facts. No new retrieval/ranking measurement is performed.

Nine provider calls complete with zero provider errors, timeouts or retries, but
one of four application requests fails validation. Usage is 26,972 input and 2,157
output tokens (29,129 total), versus 41,677 in the baseline. Fewer calls reflect
the failed case and the local refusal, not a demonstrated efficiency gain. Billed
cost remains unavailable without billing evidence.

| Nonstreaming timing (seconds) | n | Mean | P50 | P95 |
| --- | --- | --- | --- | --- |
| Successfully returned planning stage | 3 | 3.873 | 4.397 | 4.410 |
| Assessment | 3 | 2.836 | 2.702 | 3.316 |
| Generation or local refusal | 3 | 0.961 | 1.436 | 1.445 |
| Component sequence, including failed case | 4 | 8.057 | 8.882 | 9.220 |

The failed planning call's provider duration is retained in events and its request
total; no successful stage duration is fabricated. Generation/refusal includes two
provider calls and one local bypass. Percentiles use linear interpolation. Queue
time is included but not isolated, concurrency is one and no local model loads.
These are not HTTP response or streaming first-delta latency measurements. Indexing,
supplementary retrieval, saved history and serving throughput are not exercised.
[All 20 metrics](measurement.json) distinguish scope, unavailable semantic scores,
all-intended delivery and completed-only quality.

## Records and limits

[Protocol](protocol.md) was frozen before requests, with both historical protocols
preserved verbatim. [Preparation](preparation.json) records committed product code,
safe settings, device and input hashes. [Provider events](provider-events.jsonl)
retain exact inputs/outputs, revision, usage and timing, including the invalid plan.
[Artifact review](artifact-review-1.json) checks event accounting, frozen hashes,
metric completeness, English content, links and formatting. Product code was not
changed during this run.

One Codex /root reviewer performed semantic review; no independent second or human
review is available. Each development question ran once. Prompt changes and model
variability limit causal attribution, so the observed regression is not proof that
the prompt alone caused it. No repeatability, held-out quality, end-to-end acceptance
or merge approval is established. Prior failures remain intact.
