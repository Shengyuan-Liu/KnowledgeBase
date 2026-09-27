# Evidence Sufficiency and Supplementary Retrieval

Status: v2 stage 4 implemented and offline-tested. **Plan complex questions**
and API/CLI `planned` mode now assess each required point after packing evidence,
then search for remaining gaps within the same request limits. Ordinary `single`
mode is unchanged. Live assessment accuracy, answer quality, latency and cost
remain unmeasured; implementation checks do not imply acceptance or merge.

## Source-based assessment

`rag/sufficiency.py` defines four statuses per original requirement:

| Status | Meaning and required output |
| --- | --- |
| `supported` | All requested detail is supported; exact source quotes and an empty gap |
| `partial` | Some detail is supported; source quotes and a specific remaining gap |
| `missing` | No relevant support; a gap with no supporting quotes |
| `conflicting` | Unresolved incompatible statements; at least two distinct source quotes and a conflict description |

The assessor sees the exact packed answer context, a catalog of canonical offsets
and evidence IDs, the original/resolved question, requirements, executed queries,
pending dependencies and remaining limits. It does not see excluded candidates.
The catalog includes expanded parent text and separately supplied PDF table labels,
headers and other supplements. Text occurs once in the model payload; the local
record retains the canonical slices for provenance review.

Every requirement must appear exactly once. Referenced IDs must belong to the
current context and quotes must match exact source substrings. The application
records file identity/name and canonical quote offsets. These checks establish
provenance, not whether a quote actually proves the requested fact. Source names,
rankings, citations and well-formed structured output are not correctness labels.
Semantic support, conflict detection and query reformulations remain fallible model
assessments. The prompt requests no reasoning trace or confidence percentages.

## Bounded gap searches

The existing `services/hops.py` controller now also handles independent and direct
plans. It assesses the first packed context and every subsequent round. If all
requirements are supported, it stops immediately. Otherwise it may execute pending
source-bound dependencies and supplementary queries in the same next round, giving
existing dependency nodes priority when the query budget is tight.

Supplementary queries can only reference unresolved, existing requirements. A
question reformulation is instructed to preserve the user's entities, years and
scope. A new source-derived target requires exactly one `{target}` placeholder and
verbatim references containing that target; the application performs substitution.
No model can provide file IDs or expand the frozen Ready-file boundary. Literal
quote validation does not prove that a template expresses the right relationship,
or that a target-free reformulation follows the semantic prompt restrictions.

Repeated supplementary text is excluded before embedding. Repeated dependent text
continues to share its prior execution. All executed logical query IDs, including
aliases, count toward the six-query limit. Excluded proposals retain their reasons
(`duplicate`, `evidence_unavailable` or `query_limit`). Prior candidates are repacked
under one global evidence budget; earlier support is never carried forward as a
fact when its source is absent from the final context. Direct plans also merge
new candidates when supplementary searches run.

| Control | Default and behavior |
| --- | --- |
| `PLANNING__SUFFICIENCY_ENABLED` | `true` in planned mode; `false` is the stage 3 controller ablation |
| `PLANNING__MAX_ROUNDS` | 3; may be lowered to 1 or 2 |
| Total logical queries | At most 6 across initial, dependent and supplementary execution |
| Planning | One initial structured call |
| Target binding | At most one batch call before each later round; at most 2 total |
| Assessment | At most one call per round; at most 3 total; no call for an empty context |
| Request time and tokens | Existing planner caps, request deadline and answer reserve apply to all stages |
| Provider retries | Zero; invalid schemas, unknown IDs and invented quotes fail without repair |

The same planner model performs assessment with prompt version
`evidence-sufficiency-v1`. The existing request deadline includes assessment and
supplementary retrieval; limits do not restart between rounds. An empty context
gets a deterministic all-missing assessment. A refresh with no eligible new query
can consume a round to reassess a changed context without another embedding call.
Missing/ambiguous dependency bindings may be reconsidered in a later round after
new source text arrives, within the same limits and prerequisite-source rules.

Stop reasons are `requirements_supported`, `round_limit`, `query_limit`,
`no_new_evidence` and `no_eligible_query`. No progress means no new canonical source
characters in packed evidence, not merely unchanged chunk IDs. Even the last round
is assessed before answering. `requirements_supported` is the assessor's decision,
not independent verification of the final answer.

## Final answer, progress and history

The final answer uses one frozen source context. It receives short requirement
statuses and gaps as fallible guidance, explicitly separated from source evidence.
Partial support leads to supported details and stated limits; conflicting statements
must be cited separately without an invented resolution. An all-missing assessment
returns the standard insufficient-evidence message without an answer-model call.
A false all-missing assessment can therefore cause incorrect abstention; live
acceptance must measure this separately from appropriate abstention.

JSON, SSE and CLI share this controller. SSE exposes **Checking evidence…** between
search rounds and publishes exactly one final sources event. Timeout/cancellation
prevents later searches and saving an unfinished turn; an already in-flight
synchronous call may still complete and consume tokens. Models run outside database
sessions. Each new retrieval step refreshes Ready status; a source removed before
a supplementary target is used cannot authorize that search. Deletion after final
retrieval retains the same historical frozen-source behavior as existing chat.

Completed snapshots use `retrieval.planning.version=3`, with the final `assessment`
and every round's assessments in `hops.assessments`. Records include exact context,
source quotes, proposed/excluded/executed queries, rankings, packing exclusions,
model inputs/outputs, model identity, usage when supplied, timings and stop reasons.
Earlier version 1/2 snapshots remain readable. No migration or reindex is required.
The Search plan panel shows each status, gap and source quote, with an explicit
notice that model labels may be wrong. Saved history restores the same assessment.

## Verification and limitations

The [verification record](../evals/check-runs/20260926-sufficiency/README.md)
retains every failed/successful command, an offline before/after controller ablation,
source-span metrics, browser screenshots and the complete measurement inventory.
The comparison freezes questions, corpus, labels, vectors and initial plans; only
sufficiency control changes. Its hand-authored assessments test control flow, not
model accuracy. Mock answer placeholders are not answer-quality measurements.

The feature is ready for a separate live acceptance workload covering false
sufficiency, incorrect abstention, conflict interpretation, unnecessary searches,
actual answers/citations, first-answer-delta and complete-response latency, usage
and cost. OCR, visual figure interpretation and formula understanding remain outside
v2. Existing PDF extraction fidelity limits also remain in effect.
