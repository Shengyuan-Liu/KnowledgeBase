# Answer-rule separation: bounded live component acceptance

Freeze product commit 5447c29 and use the existing authorized local credential.
Test four questions once each with gpt-4.1, sequentially, with zero provider retries.
Use production PlanningOptions and generation limits. Retain every attempt and
do not rerun failures or change prompts during this run. No paid judge is used.

Reuse the exact packed evidence from the planned grouped/blank-cell request in
20260927-blank-plan-acceptance. It is a frozen digital PDF table for November 2015,
with Alabama Handgun 23,022, Pre-Pawn Handgun 14, Rentals Handgun blank, and Rentals
Long Gun blank. Original page annotations, cell/header bindings and PDF identity
remain in that run. No upload, new retrieval, reranking, packing or indexing is
performed. The fixed-context design isolates planner and assessor classification.

## Questions and gates

1. Exact prior failure question, including its conditional answering instruction:
   all four factual points retained; instruction in answer_rules rather than a
   factual requirement; four supported facts; correct, individually cited answer.
2. Same four points with a paraphrased answering instruction: same gates.
3. A factual conditional question: if the Rentals Handgun cell is blank, ask for
   the ungrouped Handgun value and whether the document explains the blank. Keep
   the blank/value/explanation as factual requirements, not answer_rules. Support
   the two available facts and disclose that no explanation is supplied. Partial
   or missing explanation is expected; do not invent a cause.
4. Ask for Alabama Handgun and Pre-Pawn Handgun for November 2016, with a rule to
   disclose insufficient evidence. The frozen table is November 2015. Preserve
   both requested facts and the year; separate the rule; mark unsupported facts
   missing and abstain without substituting 2015 values.

The exact wording and expected points are frozen in cases.json before requests.
One Codex /root reviewer inspects every actual answer, plan, assessment, reference
and supplied context. Score each expected point 0/0.5/1 for incorrect/partial/full
delivery; classify each factual sentence/list item for support and inline citation.
Missing-information statements are reviewed separately. No independent second or
human review is available. LLM assessments are not ground truth.

## Component boundary and comparison

Run the actual planner, then the actual HopController.assess on the fixed evidence
as a final round (round_index=3), then the actual bounded generate_answer function.
Clear historical executed queries; no new query is claimed to have executed.
Supplementary retrieval is disabled by this final-round boundary. A stop reason of
round_limit on missing information is expected under this harness; it does not
test the application's full multi-round retrieval behavior. Preserve dependencies
and any query proposals; they are observations, not executed searches.

The first question has the exact historical before result. Its context and fact
annotations match, but the baseline was a full API request with executed-query
metadata and first-round assessment. The new run is a final-round component replay;
these metadata differences and model variability limit causal attribution. The
other three questions are new development controls, with no historical baseline.
One attempt per question does not establish statistical stability or generalization.

Retain source hashes, committed product version, harness hashes, safe settings,
exact SDK inputs/outputs and revisions, evidence, timings, errors and token usage.
Report all 20 measurement-policy metrics: retrieval ranking and ingestion are not
applicable; supplied-context coverage and answer review remain separate. Nonstreaming
component durations are not HTTP latency or first-answer-delta latency. Report
stage and component total n/mean/P50/P95 using linear interpolation, concurrency
one, local device and provider-call boundaries. Provider queue time is included
but not isolated; no local model loads. Billed cost is unavailable without billing
evidence. Passing this subset does not authorize merge or general v2 acceptance.
