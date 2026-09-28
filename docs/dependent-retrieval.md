# Evidence-dependent Retrieval

Status: v2 stage 3c implemented and offline-tested. The existing **Plan complex
questions** checkbox and API/CLI `planned` mode can now follow a dependency chain.
Stage 4 now adds [sufficiency grading and supplementary searches](evidence-sufficiency.md)
to dependent, independent and direct planned routes. Set
`PLANNING__SUFFICIENCY_ENABLED=false` for the stage 3 behavior described below.
Live planning, answer quality, latency and whole-turn cost have not been evaluated.

## From a plan to a grounded search

For “Where is the institute employing the Aster Prize winner located?”, a plan
can declare:

1. Search for the winner.
2. Search `Who employs {target}?`, depending on the winner query.
3. Search `Where is {target} located?`, depending on the employer query.

The initial planner supplies templates and dependencies, not guessed names.
Before round 2, a separate bounded structured call can bind `Mira Cole` only if
that exact string occurs in a quoted passage from round 1. Before round 3, it can
bind `Birch Institute` only from the employer query's retained passages. These
names and example documents are synthetic test data, not factual claims.

The application substitutes the extracted target into the fixed template. The
binding model cannot rewrite the search or select file IDs. Initial planner
instructions preserve names, years, file restrictions and bridge requirements;
model adherence to those semantic instructions remains a live evaluation concern.

`rag/planning.py` validates the graph: unique IDs, known earlier prerequisites,
coverage of all required points, at least one initial query, no cycles, no more
than three levels and six total query nodes. Independent/direct plans cannot
contain dependencies. Every template contains exactly one literal `{target}`.
Tasks needing multiple simultaneous target substitutions require separate queries
or narrowing; an arbitrary query-generating agent is outside this contract.

## Binding and provenance

`rag/dependencies.py` prepares excerpts only from the current packed context and
only where a prerequisite query contributed a child hit. Expanded parent passages
and separately located PDF supplements may qualify. Raw candidates excluded by
packing are never supplied to the binding model. Every prerequisite must have a
retained excerpt before the dependent node can be attempted.

A binding decision is `resolved`, `missing` or `ambiguous`. A resolved decision
must cite exact quotes from that node's assigned excerpts, and its target must be
a literal substring of each quote. The application checks this before running any
query in the batch, then records evidence ID, file ID/name and canonical quote
offsets. Quotes and targets are case-sensitive. A passage mentioning a name does
not by itself prove the intended relationship: exact-source checks validate
provenance, not semantic correctness. The model is instructed to reject missing,
conflicting or ambiguous relationships; those judgments remain assessments.

Missing/ambiguous decisions carry no target or references. They do not trigger
searches or repair calls. Invalid IDs, invented quotations or targets absent from
the quotes fail the request without saving a completed answer. Source text is data,
not controller instructions. Model-produced intermediate prose never becomes an
answer source; only canonical source text enters the final context.

## Bounded execution and lifecycle

`services/hops.py: HopController` advances one round at a time. All independent
nodes ready at the same level share one binding call. Each model call runs outside
a database read/write session. Retrieval uses fresh read sessions and the original
Ready-file boundary; uploads cannot expand it. A subquery can narrow that scope.
A dependency requiring a file outside it records an unresolved search rather than
opening the scope.

Before binding, the controller drops ineligible files from prior runs and repacks
eligible evidence. It rechecks quote-source eligibility after the binding call, so
a file deleted during that call cannot authorize the next search. Old round
snapshots preserve what was actually seen; final sources use the current eligible
pool at the last retrieval step. As with other chat paths, deletion after final
retrieval does not retroactively change an answer already being generated.

All rounds reuse the existing retrieval, optional reranking, cross-query merge,
requirement/document selection, parent expansion and evidence packing. Repeated
query text with equivalent scope shares an execution, even across rounds, and does
not add extra ranking votes. Each round repacks the accumulated eligible candidates
under the same global evidence budget; contexts are never concatenated.

| Limit | Applied behavior |
| --- | --- |
| Six total query nodes | Initial plus dependent nodes; validation rejects oversized plans |
| `PLANNING__MAX_ROUNDS=3` | May be lowered to 1 or 2; hard maximum is 3 |
| One planning call | Same opt-in planner; now uses `dependent-planner-v5` |
| At most two binding calls | One per subsequent round, using `dependency-targets-v1` and the same planner model |
| Existing per-call caps | Planner/binding calls share input/output and timeout controls |
| Existing request deadline | Includes resolution, planning, binding, retrieval and final generation; retains the answer-time reserve |
| Existing evidence budget | Default 4096 tokens including labels and PDF supplements, independently enforced on every repack |
| Zero planned-provider retries | No fallback model or additional planning loop; one recorded coverage query can complete an unassigned decomposed requirement within the existing limit |

The round limit does not multiply token budgets or extend the total deadline.
Cancellation during binding prevents later queries and persistence. Already
in-flight synchronous calls may finish and consume provider tokens; the existing
[deadline and cancellation limits](planned-retrieval.md#request-bounds) still apply.

Stop reasons are execution outcomes, not sufficiency assessments:

- `dependencies_complete`: all dependent searches were attempted without an
  unresolved scope/binding; this does not mean every answer point is supported.
- `dependency_unresolved`: a required target, prerequisite excerpt or allowed scope
  was unavailable/ambiguous. Downstream nodes are marked blocked.
- `round_limit`: pending work remains after the configured number of rounds.
- `no_new_evidence`: another round cannot proceed because the packed context added
  no previously unseen canonical source characters. Different chunk IDs, rankings
  or duplicate queries alone do not establish progress.

The final answer is generated once from the frozen final context using the existing
instructions to address each requested part and identify missing support. This
stage does not add a semantic sufficiency grader. A bridge used earlier can be
excluded by later packing; `references_in_final_context` explicitly reports that
condition. A successful target binding is not permission to state a fact absent
from the final supplied excerpts.

## Chat, history and UI

JSON, streaming chat and CLI share the controller. No reindex or database migration
is needed. Dependent requests save `retrieval.planning.version=2`, adding `hops`:

- the original plan and prerequisite IDs;
- every round's query-local ranks, selected candidates, packed sources, exclusions
  and exact context;
- binding prompts/outputs, model IDs, response IDs, per-call limits, timings and
  provider usage when returned;
- targets, exact source references, unresolved/blocked states and the stop reason.

`retrieval.planning.trace` remains the final accumulated executor trace. Existing
version 1 independent snapshots remain readable. Citation numbers are assigned
only after all rounds stop. SSE sends `Searching round N…` progress before each
step and exactly one final `sources` event; JSON, SSE completion and saved history
agree on the final record. The plan panel displays each derived target, its quote
and source filename, with a notice when the quote is absent from final context.
Refresh restores the same trace without rerunning retrieval. Deletion preserves
historical quotes; original PDF access follows the usual file lifecycle.

## Verification and remaining limits

The [stage 3c run record](../evals/check-runs/20260926-dependent-retrieval/README.md)
retains all attempts, scoped/full offline suites, browser traces/screenshots and
a frozen controller comparison. The controlled after route supplies two-/three-hop
facts missed by its direct control. Source scope and an exhausted evidence budget
still limit coverage. All plans, target decisions and vectors are frozen mocks;
these results establish mechanics, not live LLM quality.

The comparison holds corpus/questions/span labels/settings fixed. The before route
replays the preceding version's direct decision for dependent questions through
the unchanged direct path; it uses current code/prompt metadata rather than an old
binary or live model. Whole-turn provider usage/cost and production latency remain
unavailable. A future acceptance run must evaluate target semantics, actual answers,
citation support and coverage separately, including cases where a bridge is lost.
