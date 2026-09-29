# Evidence Sufficiency and Supplementary Retrieval

Status: v2 stage 4 implemented, offline-tested and development-evaluated with
real PDFs. The [live comparison](../evals/library-runs/20260927-v2-pdf-live/README.md)
does **not** pass acceptance: that repaired planned mode completed 15/16 turns.
Financial packing and assessor quote selection have since received repairs and a
[six-request financial replay](../evals/library-runs/20260927-financial-acceptance/README.md).
All six requests complete with correct requested facts, but one planned income
bullet still lacks an inline citation, so the scoped citation gate fails.
The subsequent [offline citation/context repair](../evals/check-runs/20260927-citation-context/README.md)
adds source-number guidance and explicit table context; model citation compliance
was then remeasured in a [six-request follow-up](../evals/library-runs/20260927-financial-citation-acceptance/README.md).
All scoped gates pass under the prior review rules, including their allowance for
fiscal-period inference. The report distinguishes these inferences from literal
table statements; the historical failure and broader acceptance limits remain.
**Plan complex questions**
and API/CLI `planned` mode now assess each required point after packing evidence,
then search for remaining gaps within the same request limits. Ordinary `single`
mode remains available. Live quality, latency and token usage are recorded;
billed cost and independent human review remain unavailable. Implementation and
test completion do not imply acceptance or merge.

## Source-based assessment

`rag/sufficiency.py` defines four statuses per original requirement:

| Status | Meaning and required output |
| --- | --- |
| `supported` | All requested detail is supported; source passage IDs and an empty gap |
| `partial` | Some detail is supported; passage IDs and a specific remaining gap |
| `missing` | No relevant support; a gap with no supporting references |
| `conflicting` | Unresolved incompatible statements; at least two distinct source passages and a conflict description |

The assessor sees the packed answer context with inline passage markers such as
`[p1]`, plus the original/resolved question, requirements, executed queries, pending
dependencies and remaining limits. Each marker identifies one nonblank source line;
its original whitespace and line ending are preserved. Blank lines are preserved
without selectable IDs. IDs are local to that assessment. Expanded parent text and
separately supplied PDF labels, headers and other supplements are eligible; excluded
candidates are not. Source metadata, table coordinates, supplement roles and
extraction warnings remain visible. Text occurs once in the model payload.

The full local catalog maps these short IDs to original text, canonical offsets,
source numbers and file identities. PDF passages also retain zero-based physical
page indices from overlapping stored regions. These are the existing parser's
regions, not new line-accurate bounding boxes. The answer context is unchanged;
only the assessor's view receives passage markers.

Every requirement must appear exactly once. Referenced IDs must belong to the
current catalog. Model references contain only `evidence_id`; the application
resolves the quote, file identity/name, offsets and PDF pages from that catalog.
The model cannot supply or rewrite quote text or positions. Headers, distant values
and units can be selected separately, without stitching a fabricated quote.
For selected PDF table passages, the application also attaches already-supplied
column headers and table captions, notes or adjacent text as `table_context`.
Parser header spans and table IDs define these links; no new source text is fetched.
Each attachment retains its exact quote, location, role and selected-passage IDs.
This context is separate from model-selected `references`, does not change the
assessor's status, and cannot satisfy conflict counts or supplementary-query target
checks. Association with a table is not proof that a passage supports the answer.
These checks establish
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
selected passages containing that exact target; the application performs substitution.
No model can provide file IDs or expand the frozen Ready-file boundary. Literal
target validation does not prove that a template expresses the right relationship,
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
| Provider retries | Zero; invalid schemas, unknown passage IDs and unbound targets fail without repair |

The same planner model performs assessment with prompt version
`evidence-sufficiency-v5`. It scores only the supplied factual requirements;
answering instructions remain outside that set. The planner separately records
`answer_rules`, while original user instructions remain in the generation question.
A factual conditional question still needs source evidence. Missing or partial
factual points continue to trigger the existing bounded-search/abstention behavior.
The [answer-rule regression](../evals/check-runs/20260927-answer-rules/README.md)
replays the observed conditional-rule mistake with explicitly annotated provider
outputs. It checks controller behavior and preservation of real missing-evidence
handling, not live model classification accuracy. The subsequent
[four-case live component acceptance](../evals/library-runs/20260928-answer-rules-acceptance/README.md)
fails two gates: a factual conditional question gains an invented answering rule,
and a November 2016 question is incorrectly supported and answered with November
2015 values. The exact original rule and its paraphrase pass. Fixed evidence and
final-round assessment isolate these components; full multi-round behavior and
broader quality are not established. Valid source offsets do not prove temporal
or semantic support.

The [period/rule constraint regression](../evals/check-runs/20260928-period-rule-constraints/README.md)
adds explicit document/entity/period/column matching instructions to assessment and
generation. Other-period values alone must be missing, with the mismatch stated;
they do not establish partial support for the requested period. Multi-period
requirements may be partial when at least one requested period is actually present.
Period/header passage selection is requested alongside dated values. This is a
semantic instruction, not a deterministic date validator: the frozen erroneous
assessment still passes provenance validation. Offline annotated missing decisions
exercise abstention without establishing new live model accuracy.

The [matched four-case live follow-up](../evals/library-runs/20260928-period-rule-acceptance/README.md)
withholds the unavailable 2016 values and preserves all 13 expected answer points,
but only three case gates pass. The missing-year plan still transfers "ungrouped"
to Pre-Pawn Handgun and adds an evidence-availability requirement that duplicates
the answering rule. That extra supported requirement prevents the local all-missing
bypass; a model-generated limitation still answers correctly. Rule text provenance
is therefore insufficient to establish semantic separation. This remains a
fixed-evidence component result, with one Codex reviewer and no full-loop acceptance.

The [planner fact-scope update](../evals/check-runs/20260928-planner-fact-scope/README.md)
clarifies that checking whether each fact has enough evidence is the assessor's
responsibility, not another planned requirement derived from an answering rule.
Its annotated two-fact regression reaches the existing all-missing response without
generation. The actual prior three-requirement output remains reproducible; this
offline result does not prove the revised planner will emit the intended plan.

The [matched fact-scope live run](../evals/library-runs/20260928-planner-fact-scope-acceptance/README.md)
removes the missing-year plan's duplicate availability requirement and reaches
the local all-missing response, but retains the wrong Pre-Pawn qualifier. A separate
factual-condition request regresses to a planner validation error: dependent
templates omit their required target placeholders. Only 3/4 requests complete,
2/4 case gates pass and 10/13 intended points are delivered. The failed case has
unavailable semantic scores; it is not counted as a refusal or a correct answer.

The subsequent [dependency-contract offline update](../evals/check-runs/20260928-planner-dependency-contract/README.md)
adds the missing target-presence constraint to the planner schema and concrete
examples for logical conditions and column modifiers. It preserves all three
factual requirements in an annotated independent plan, including the explicit
explanation question. It changes neither assessment nor generation. The raw
qualifier error remains accepted; this update has no new live quality result.

The [matched dependency-contract live follow-up](../evals/library-runs/20260929-planner-dependency-acceptance/README.md)
recovers four completed answers and all 13 expected points. The condition uses
independent queries, its missing explanation is correctly disclosed, and the
missing-year plan preserves both column paths before reaching the local refusal.
Only 3/4 gates pass: the factual condition is also copied into `answer_rules`.
Exact original text passes provenance but does not establish correct semantic
classification. This new regression is retained without an in-run product repair.

The assessment contract distinguishes question-provided file names from new
source-derived targets and selects passage IDs instead of generating free-form
quotes. Dependency target binding remains on its existing separate contract.
The [offline passage comparison](../evals/check-runs/20260927-assessment-passages/README.md)
retains the prior live quote failure and checks the new contract on frozen inputs.
Hand-authored passage selections do not establish live model accuracy. The later
financial replay records real ID selections and source-supported requested facts
on three development questions; it does not establish general assessor accuracy.
The existing request deadline includes assessment and
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
It also receives `source_ids` locating selected references and attached context in
the current numbered sources. Numbers are derived from file identity and supplied
spans, including PDF supplements, rather than copied from an earlier assessment.
These are navigation hints; the generator must verify actual support. A final
format example repeats the same citation in each separate factual item, including
when one requirement covers multiple reporting periods. Generated text and stream
deltas remain unchanged by the application; these prompts do not enforce coverage.
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
model inputs/outputs, the full passage catalog, model identity, usage when supplied,
timings and stop reasons. The stored assessment context remains the unannotated
answer context; the recorded model input contains the annotated view.
Earlier version 1/2 snapshots remain readable. No migration or reindex is required.
The Search plan panel shows each status, gap and source quote, with an explicit
notice that model labels may be wrong. Saved history restores the same assessment.
When attachments exist, it distinguishes **Selected passages** from **Table context**
and identifies the latter as application-added. Older snapshots without this field
remain readable. New retrieval reconstructs header spans from stored extraction;
historical snapshots are not retroactively enriched or rescored.

## Verification and limitations

The [verification record](../evals/check-runs/20260926-sufficiency/README.md)
retains every failed/successful command, an offline before/after controller ablation,
source-span metrics, browser screenshots and the complete measurement inventory.
The comparison freezes questions, corpus, labels, vectors and initial plans; only
sufficiency control changes. Its hand-authored assessments test control flow, not
model accuracy. Mock answer placeholders are not answer-quality measurements.

The [live development record](../evals/library-runs/20260927-v2-pdf-live/README.md)
retains failed attempts, a targeted repair, same-question replay, reviewed answers
and citations, separate streaming/completion timings and actual provider usage.
It exposes false support, incorrect abstention and unnecessary supplementary work.
It does not establish genuine-conflict accuracy, a held-out quality gain or a
production latency target. The later financial repair replay recovers the missing
sales evidence and completes the formerly failing income request, while retaining
an inline-citation coverage gap. The later citation follow-up covers all 16 current
factual groups under the unchanged rubric, including the formerly uncited income
item. Model source selection remains fallible even when application-added headers
make the selected table easier to inspect. Dense-table omissions remain unresolved.
OCR, visual figure interpretation and formula
understanding remain outside v2; existing PDF extraction fidelity limits remain.
