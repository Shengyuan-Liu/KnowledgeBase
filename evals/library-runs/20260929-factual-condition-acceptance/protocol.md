# Factual condition classification: matched live component acceptance

Freeze product commit 5541597 and compare with the immediately preceding
[live run](../20260929-planner-dependency-acceptance/README.md). Preserve its
[protocol](baseline-protocol.md) and the original [rubric](frozen-original-protocol.md).
Questions, order, runner, frozen PDF evidence, annotations and runtime settings
remain identical. The only product changes are planner v8 instructions and the
answer_rules schema description; field types, limits, runtime validation,
assessment v5, generation and dependency execution are unchanged.

Run four cases once each, sequentially, with the previously authorized credential
and requested model gpt-4.1. Record the resolved revision. Zero provider retries,
no automatic repair, no paid judge, at most 12 SDK calls. Preserve every error and
do not rerun for a better score. Freeze this protocol before any paid call and
make no product changes during the run.

The baseline completes 4/4 and delivers 13/13 answer points but passes only 3/4
case gates. It correctly uses independent queries and preserves column names,
yet duplicates the factual conditional question into answer_rules. Exact text
provenance passes but semantic classification fails. Keep that failure visible.

Apply the same four gates, without relaxing the criteria:

1. Original rule: four requested cells, correct document/entity/period/columns,
   actual user answering instruction kept separately, correct individually cited
   answer, no duplicate evidence-sufficiency requirement.
2. Paraphrased rule: the same facts and behavior, with the actual paraphrased
   instruction retained and no invented instruction.
3. Factual condition: blank/value/explanation remain three factual requirements
   and independently specified queries; answer_rules is empty. Support the two
   available facts and disclose the missing explanation without inventing a cause.
4. Missing year: two November 2016 values, distinct ungrouped Handgun and Pre-Pawn
   Handgun column paths, actual limitation instruction separated, both unavailable
   values withheld. The existing rubric accepts the generic local full-question
   refusal if all-missing is reached, without inventing values or citations.

Use the same packed November 2015 PDF table in production planning, final-round
assessment (round_index=3, no executed-query metadata) and bounded generation.
No upload, retrieval, reranking, supplementary search, index, history, HTTP,
streaming or load test occurs. A generated query is a proposal, not an executed
search. This frozen-context comparison does not establish full-loop behavior.

One Codex /root reviewer reads every plan, query, assessment, answer and actual
context against unchanged source annotations. Preserve expected-point and
claim-level support/citation judgments, with absence statements separately reviewed.
No independent human or second review is available. Score expected points with
the unchanged 0/0.5/1 rubric; a failed request has unavailable semantic scores and
zero delivered points in the all-intended denominator, not a correct refusal.

Retain all 20 policy metrics with measurements or explicit scope reasons, exact
SDK requests/responses, resolved revisions, safe settings, hashes, errors, usage
and device. Report component and stage durations separately (n/mean/P50/P95,
linear interpolation); provider queue time is included but not isolated, with
no local model loading. Component totals are not HTTP or first-answer-delta
latency. Billed cost remains unavailable without billing evidence. A local
refusal has no generation provider call or fabricated token usage.

This is one development regression pass on reused questions whose wording is now
represented in prompt examples. It does not establish repeatability, held-out
generalization, isolated causality, user acceptance or merge authorization.
Preserve improvements and regressions. If all gates pass, a later step can test
new questions through the complete retrieval chain. If classification still
fails, review the rule-classification design before another prompt iteration.
