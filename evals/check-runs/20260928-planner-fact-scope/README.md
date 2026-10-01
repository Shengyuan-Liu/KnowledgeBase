# Planner fact scope and local column modifiers

The latest [live follow-up](../../library-runs/20260928-period-rule-acceptance/README.md)
answers the missing-year question correctly but plans three requirements for two
requested values. R3 repeats whether the excerpts establish the values; its
supported status prevents the all-missing generation bypass. The plan, query and
answer also transfer "ungrouped" from Handgun to Pre-Pawn Handgun.

## Changes

Planner v6 distinguishes requested source facts from the assessor's task of
checking evidence sufficiency. A conditional instruction to state a limitation
belongs only in `answer_rules`; restating its condition as an availability or
verification requirement is explicitly disallowed. A user who actually asks
whether a document reports or explains something still gets that factual requirement.

The planner now explicitly treats each independently named column in a coordinated
list with its own locally attached modifiers. Shared document/entity/period
constraints are repeated separately. Final generation also checks original column
names when describing unavailable values, because assessment descriptions may
repeat a planner's qualifier error.

These are prompt changes. No semantic keyword filter, extra provider call,
validation rejection, output-repair pass or persisted-schema change is introduced.
Existing exact-copy validation of answer rules remains. Model compliance with the
new distinctions is not established by offline tests.

## Controlled comparison

[Frozen case](frozen-case.json) preserves the exact prior model outputs and their
source artifact's SHA-256. The desired annotation removes R3 and its associations
from Q1/Q2, removes "ungrouped" only from the Pre-Pawn description/query/gap, and
retains the user rule, two queries, document, entity, November 2016 constraint and
both missing statuses. No evidence text changes.

| Input supplied to current code | Recorded decisions | Annotated intended decisions |
| --- | --- | --- |
| Requirements | 3 | 2 |
| Queries | 2 | 2 |
| Assessment statuses | missing, missing, supported | missing, missing |
| User rules | Same exact user instruction | Same exact user instruction |
| Mock provider calls | 3, including generation | 2, no generation |
| Final response | Prior generated limitation, including wrong qualifier | Local insufficient-evidence response |

[Comparison artifacts](comparison-1/summary.json) retain both plans, exact current
requests, assessments and context hashes. Both arms use current code with controlled
provider responses. The prior bad plan and answer remain reproducible; they are
not silently corrected. The annotated output is a development expectation, not a
new model result. The existing local refusal is less specific than a generated
period explanation, so bypassing generation is not itself an answer-quality gain.

Three additional controls replay the previously accepted original-rule,
paraphrased-rule and factual-condition plans. The explicit document-explanation
question retains all three requirements, including the explanation check. This
verifies typed-plan preservation, not fresh model classification.

## Checks and limits

- [Focused check](focused-1.json): 97 passed, 0 failed, 0 skipped; pytest duration
  4.42 seconds.
- [Scoped check](scoped-1.json): 294 passed, 0 failed, 0 skipped; pytest duration
  9.75 seconds. Planning, PDF/table evidence, retrieval, document scope, sufficiency,
  chat, streaming and citations are covered. One existing Starlette/AnyIO
  deprecation warning remains.
- [Comparison command](comparison-1-check.json): passes; equal evidence text/catalog,
  exact question/rule retention and generation bypass for the annotated two-fact plan.
- [Documentation review](documentation-1.json): content, local links and formatting.
  A stale planned-retrieval statement about unimplemented sufficiency was also
  corrected to link the existing implementation.

All commands record base commit `6bdcf47`, uncommitted file hashes, exact command,
device, duration, output, counts and the complete 20-metric inventory. These are
mocked offline checks: live answer quality, provider cost, production latency,
throughput and ingestion are not applicable. No evidence-coverage score is invented
for absent 2016 facts. Context equality is a structural observation only.

Reviewer: Codex /root; annotations are not human ground truth or independent review.
No paid calls, retrieval rerun or live acceptance occurred. Preserve the prior
failed acceptance until a bounded matched live comparison tests actual planner
and answer behavior. This update remains on v2 and does not authorize a merge.
