# Separate answering rules from factual requirements

The previous [live acceptance](../../library-runs/20260927-blank-plan-acceptance/README.md)
answered all four grouped/blank-cell points, but its planner made the instruction
"If the supplied excerpts do not establish a requested cell's contents, state that
limitation" a fifth factual requirement. The assessor marked it missing while
also reporting that every requested cell was established. That produced the
misleading controller stop reason `no_eligible_query`.

## Implementation

`dependent-planner-v4` separates source-verifiable `requirements` from
`answer_rules`. Rules remain in plan/history records; they have no requirement IDs
and do not create evidence gaps or additional coverage queries. The unchanged
original question still carries the user's instructions into answer generation.
`evidence-sufficiency-v4` assesses only factual requirements. Genuine conditional
fact questions still need evidence, and genuine missing evidence still permits
bounded supplementary retrieval or abstention.

Historical plans may omit the new field and read with an empty list. New strict
provider schemas require the list explicitly. There is no text-pattern filter,
automatic correction of old model outputs, or rewriting of historical evidence.

## Controlled comparison

[Frozen case](frozen-case.json) retains the exact prior planner/assessor outputs
and the source artifact's SHA-256. Codex /root annotated an expected classification
by moving only R5 into `answer_rules` and removing its query associations. The four
factual requirements, four query texts, source facts, context and evidence catalog
stay fixed. Both arms run the current controller with mocked provider outputs;
this is a contract comparison, not a before/after live-model experiment.

| Observation | Recorded classification | Annotated separation |
| --- | --- | --- |
| Factual requirements | 4 | 4 |
| Answering instruction counted as a requirement | 1 | 0 |
| Retained answer rules | 0 | 1 |
| Planned queries | 4 | 4 |
| Supplied frozen facts fully covered | 4/4 | 4/4 |
| Supplementary queries | 0 | 0 |
| Controller stop | `no_eligible_query` | `requirements_supported` |

[Comparison artifacts](comparison-1/summary.json) retain exact requests, outputs,
normalized references, context hashes and source-bound cell/header/row checks.
Evidence coverage uses the original four annotations, including full-row proof
for blank cells. Equal coverage means evidence was preserved; it is not an answer
quality improvement. The old misclassified output still reproduces the old stop
reason, rather than being silently repaired.

## Verification and reproducibility

- [Focused tests](focused-1.json): 73 passed, 0 failed, 0 skipped; pytest duration
  3.60 seconds.
- [Scoped tests](scoped-1.json): 284 passed, 0 failed, 0 skipped; pytest duration
  9.40 seconds. This covers planning, scope, sufficiency, PDF/table evidence,
  retrieval, chat, streaming and citations. One existing Starlette/AnyIO
  deprecation warning remains.
- Paired API tests preserve rules in stored history and confirm that a fact
  available in the selected file is supported, while an absent location fact
  remains missing and returns the insufficient-evidence answer without generation.
- [Comparison command](comparison-1-check.json): passed; no live provider calls.
- [Documentation review](documentation-1.json): content, local links and source
  formatting reviewed separately.

Each command record includes its exact invocation, base commit `aab742f`, file
hashes for the uncommitted implementation, device, wall duration, output and the
complete 20-metric inventory. [Baseline source](baseline-code/planning.py) and
its three companion files preserve the changed components before this work.
Run `record_check.py` with a new record name to retain later commands; run
`compare.py` with a new output-directory name and `PYTHONPATH=.` from the project
root. Records and comparisons are append-only.

The comparison uses the model identifier `offline`, mocked provider responses,
sequential execution and no model revision, model loading, queue or paid usage.
Production latency, retrieval ranking, generated-answer quality, cost and load
capacity are not exercised. Coverage is measured separately in the comparison
inventory; local test duration is not a production latency measurement.

## Remaining acceptance boundary

The revised prompts have not been tested against a live model. Correct separation
in the comparison is supplied by a development annotation, so these results do
not establish that the model will classify rules correctly or consistently.
If it emits the old classification, this implementation does not repair it.
Reviewer: Codex /root; no independent second or human review. A later bounded
live acceptance should check classification and genuine factual-condition cases.
This commit stays on `v2`; user acceptance and merge authorization remain separate.
