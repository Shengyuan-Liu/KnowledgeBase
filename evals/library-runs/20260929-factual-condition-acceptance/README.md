# Factual-condition acceptance: four scoped gates pass

All four requests complete and pass the unchanged case gates. The factual
conditional question no longer appears in `answer_rules`; its three independent
fact queries and correct answer remain intact. All 13 expected answer points
are delivered, with ten positive factual groups supported and individually cited.
This is one fixed-context development pass, not full v2 acceptance.

## Matched comparison

| Case | Immediate baseline | Current result | Gate |
| --- | --- | --- | --- |
| Original rule | Four correct cells and actual answering instruction | Same four facts, separated instruction and individual citations | Pass |
| Paraphrased rule | Same four facts and actual paraphrased instruction | Same behavior without duplicate evidence requirements | Pass |
| Factual condition | Correct three-point answer, factual question duplicated into answer_rules | Empty answer_rules, three independent fact queries, complete answer | Pass |
| Missing year | Correct column paths, two missing values and local refusal | Same November 2016 scope, missing statuses and refusal | Pass |

The [immediate baseline](../20260929-planner-dependency-acceptance/README.md)
completed 4/4, delivered 13/13 points and passed 3/4 case gates. This run preserves
completion and answer quality while improving classification and case gates to
4/4. Both runs have 10/10 supported and individually cited positive factual
groups. The observed gain is the corrected rule classification, not a new answer
accuracy or evidence-coverage gain. Previous failed attempts remain unchanged.

[Semantic review](review.json) retains exact expected-point evidence, every
positive factual group, absence statements and case judgments. The original and
paraphrased questions each preserve their genuine user instruction. In
[factual-condition.json](factual-condition.json), the blank cell, Handgun value
and explicit explanation question remain three factual requirements, with three
independent queries and no dependencies or answering rules. Assessment supports
the first two facts and marks the explanation missing. The answer reports the
blank cell and 23,022 with inline citations, then explicitly limits its missing
explanation statement to the supplied excerpts. It invents no cause.

In [missing-year.json](missing-year.json), ungrouped Handgun and Pre-Pawn Handgun
remain distinct column paths, both restricted to November 2016. The evidence is
November 2015, so both requirements are missing with no references. The existing
local full-question refusal is returned without a generation call. The frozen
rubric accepts this generic refusal for both absent values; it does not name the
year or individual fields. Appropriate full abstention is 1/1, incorrect full
abstention on fully answerable questions is 0/2, and correct partial limitation
is 1/1. Absence statements are reviewed separately from positive factual claims.

## Evidence and measurement

Product version: `5541597`. Resolved model: `gpt-4.1-2025-04-14`, unchanged. The
[preflight](preflight-1.json) verifies identical questions, case order, runner,
safe settings and frozen evidence. The planner uses v8 and its new field description;
assessment remains v5 and generation is unchanged. No case was repaired or rerun.

Every assessor and executed generator receives the same 2,604-token context.
All ten available source-fact occurrences are fully covered, with exact row,
cell, period and header bindings. The unavailable year values and explanation
have no gold evidence; no zero-recall value is fabricated. Reference offsets
and attached headers match the original extraction. This unchanged context does
not measure new candidate retrieval, reranking or packing quality.

Eleven SDK calls complete: four planning, four assessment and three generation,
with zero application errors, provider errors, timeouts or retries. Usage is
38,043 input plus 2,351 output tokens, 40,394 total, versus 39,349 in the baseline.
Billed cost is unavailable without billing evidence. The increase is an observed
token total, not an estimated charge.

| Nonstreaming timing (seconds) | n | Mean | P50 | P95 |
| --- | --- | --- | --- | --- |
| Planning | 4 | 3.203 | 3.219 | 4.307 |
| Assessment | 4 | 3.330 | 3.791 | 4.024 |
| Generation or local refusal | 4 | 1.633 | 1.902 | 2.704 |
| Complete component sequence | 4 | 8.171 | 8.485 | 8.987 |

Baseline component mean/P50/P95 were 6.445/5.958/9.464 seconds. The current mean
and median are higher, while P95 is lower; four sequential samples cannot establish
a stable performance change or attribute it to the prompt update. Generation/refusal
includes three model calls and one local bypass. Percentiles use linear interpolation;
provider queue time is included but not isolated, concurrency is one and no local
model loads. These are component timings, not HTTP latency or streaming first delta.

[All 20 metrics](measurement.json) retain values or explicit scope reasons. No
new upload, embedding, search, reranking, supplementary retrieval, history,
streaming, ingestion or serving-throughput test is performed. Missing cases reach
the final-round harness boundary and stop at `round_limit`; no proposed search is
counted as an executed query. All four plans are independent, so live genuine
source-derived dependency behavior is not exercised here.

## Records and next boundary

- [Protocol](protocol.md), [baseline protocol](baseline-protocol.md) and
  [original rubric](frozen-original-protocol.md), fixed before paid calls.
- [Preparation record](prepare-1.json), [safe settings/hashes](preparation.json),
  [frozen questions](cases.json) and [frozen evidence](frozen-evidence.json).
- [Raw SDK requests/responses](provider-events.jsonl), [run output](live-1.log),
  and exact plans, assessments and answers in each case file.
- [Review record](review-1.json), [measurement command](analysis-1.json) and
  [artifact/documentation review](artifact-review-1.json).

Reviewer: one Codex /root semantic review, not independent human ground truth.
These are reused development questions whose structure appears in prompt examples.
Passing this pass does not establish held-out generalization or repeatability.
The next useful boundary is new source-anchored questions through the complete
retrieval and answer chain, including evidence selection, page citations and
appropriate abstention. That workload was not run here. Product code remains
unchanged during this evaluation, and no merge or general acceptance is authorized.
