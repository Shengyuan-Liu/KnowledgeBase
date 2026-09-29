# Factual conditions are not answering instructions

The latest [live acceptance](../../library-runs/20260929-planner-dependency-acceptance/README.md)
delivers 13/13 expected points but passes only 3/4 case gates. Its factual-condition
plan correctly retains three independent fact queries, then duplicates the factual
question into `answer_rules`. The quote is present verbatim in the question, so
the existing text-provenance check cannot identify this semantic error.

## Change

Planner v8 explicitly separates the categories in both directions. Requested
facts and their conditions remain factual requirements; they must not also become
answering rules. Answering instructions describe presentation or disclosure of
evidence limitations. Three contrasting partial-output examples cover:

- A factual condition asking why revenue fell: no answering rule.
- An instruction to state a limitation if evidence is absent: retain that rule.
- A factual condition followed by a formatting instruction: retain only the
  formatting instruction as a rule, with both facts still required.

The known-row conditional retrieval example now explicitly says `answer_rules: []`
and explains that generation receives the original question unchanged. Previously
it only said the answer should respect the condition, leaving its representation
ambiguous. This is a targeted clarification, not a demonstrated causal explanation
of the model failure. `PlanDecision.answer_rules` now has a matching provider-schema
description; its type, default, limits and runtime validation remain unchanged.

The [official prompting guide](https://developers.openai.com/api/docs/guides/prompt-engineering#few-shot-learning)
describes using input/output examples to guide classification. It does not prove
this application's classification quality. No keyword-based semantic filter,
automatic rule deletion, new provider call, retry, fallback or historical-data
rewrite is added. Assessment, generation and dependency execution are unchanged.

## Frozen comparison

[Preparation](preparation-1.json) freezes all four previous questions, outputs and
shared November 2015 PDF evidence by hash in [frozen-cases.json](frozen-cases.json).
The only authored change removes the incorrect rule from the factual-condition
decision. All facts, queries, IDs, route, original question, periods, column names,
assessments and prior answers remain fixed. The other three decisions are unchanged.
These annotations are development expectations, not newly inferred model outputs.

The [comparison](comparison-1.json) runs current production planning, final-round
assessment and generation with frozen mocked responses, once per original and
annotated arm. It also compares the archived v7 request against the current v8
request. Exact requests, outputs, plans, assessed facts, context hashes and source
hashes are retained. Both controlled arms use current code; this is not a fresh
before/after model experiment.

| Case | Original recorded decision | Annotated decision and downstream result |
| --- | --- | --- |
| Original rule | Four facts, actual answering instruction | Same plan, assessment and generation request |
| Paraphrased rule | Four facts, actual paraphrased instruction | Same plan, assessment and generation request |
| Factual condition | Three independent facts, one duplicated factual question as a rule | Same three facts and queries, empty rules; identical assessment/generation inputs |
| Missing year | Two November 2016 facts, correct column paths and actual rule | Same two missing statuses and local refusal, no generation call |

The factual condition is still present in the original question sent to generation
after removing the duplicate. Its two supported facts and missing explanation
stay unchanged. Each arm has three mock calls for the first three questions and
two for missing-year: 22 mocked calls in total, zero paid calls. The frozen answer
text is identical by construction and is not a new correctness measurement.

The original bad output remains accepted and reproducible. A schema description
and prompt examples guide the model but do not enforce semantic classification.
An additional controlled test combines the recorded factual question with the
recorded real evidence-limitation instruction, retaining only the latter as a
rule without removing any requested fact. This checks the contract, not actual
model classification of the new combined question.

Local serialized input increases by 251 `cl100k_base` tokens per case, from
1,904-1,966 to 2,155-2,217, below the unchanged 8,192-token cap. The output cap is
unchanged at 2,048. Local estimates are not provider usage or billing. Mock requests
use model `offline`; archived requests used `gpt-4.1` and resolved to
`gpt-4.1-2025-04-14`. No provider model is resolved in this run.

## Checks and limits

- [Initial focused run](focused-1.json): 59 passed, 1 failed, pytest 1.96 s.
  The new replay assertion compared the entire assessment record, including
  separately measured execution time. It now compares semantic contents and exact
  downstream requests while retaining timing records. The failed run is preserved.
- [Corrected focused run](focused-2.json): 60 passed, 0 failed, 0 skipped, pytest
  1.62 s.
- [Scoped run](scoped-1.json): 228 passed, 0 failed, 0 skipped, pytest 7.48 s.
  Covers planning, real SDK request serialization through a mock transport,
  dependencies, sufficiency, document scope, chat/API, streaming, history and
  citations. One existing Starlette/AnyIO deprecation warning remains.
- [Comparison command](comparison-1-check.json) and [documentation review](documentation-1.json)
  retain replay results and content/link/format/source-integrity checks.

Every command record includes base commit `1787b5d`, changed/tracked file hashes,
command, device, duration, counts and all 20 policy metrics with explicit scope
reasons. Live answer quality, retrieval/evidence quality, provider usage/cost,
production latency, throughput and ingestion are not applicable to mocked checks.
No test duration is reported as production performance; no missing measurement
is filled with zero. The shared evidence is unchanged, not newly retrieved or scored.

Reviewer: Codex /root, direct plan/request inspection; no independent human review.
The latest measured live result remains 3/4 case gates. The current change needs
bounded live verification before claiming semantic recovery; broader quality,
held-out evaluation and user acceptance remain open. Work stays on v2 and no
merge is authorized by these checks.
