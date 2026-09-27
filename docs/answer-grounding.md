# Answer citations and source fidelity

The shared `ANSWER_INSTRUCTIONS` in `knowledgebase/rag/generation.py` governs both
complete and streaming answers. `_answer_messages` supplies the original question,
optional conversation interpretation and numbered evidence. `generate_answer`
and `stream_answer` send the same messages through their respective clients.
The user question/evidence message precedes the developer instruction message;
source text is never promoted to developer instructions.

Factual claims should have a supporting citation in the same sentence or list
item. Each factual list item needs its own citation; an introduction, final bullet
or later summary does not implicitly cite earlier items. If different excerpts
support different claims, split the sentence or attach each citation to its claim.
Code examples use valid language comments beside source-derived lines so citations
do not alter literal values or executable syntax.

After an observed [financial PDF citation omission](../evals/library-runs/20260927-financial-acceptance/README.md),
the shared final instructions now include a two-item format example repeating the
same citation. One assessment requirement may cover several facts or periods;
citing the last item alone is insufficient. Planned answers also receive current
source-number hints for selected passages and separately attached table context.
These hints identify locations, not verified support. The
[offline regression record](../evals/check-runs/20260927-citation-context/README.md)
checks current numbering, PDF supplements and identical complete/streaming prompts.
The original failed answer remains unchanged; model compliance has not been
remeasured, and no automatic citation insertion or answer rewrite is performed.

Answers must preserve the source's stated behavior and qualifications. A field
being unsupported does not establish whether it is ignored or rejected. Missing
personal information should be identified explicitly. Next steps and contacts
may be named only when the supplied evidence provides that guidance for the
requested information; a general program description does not document how to
find a particular student's assignment or schedule.

Universal and exclusive qualifiers also need evidence: do not turn a table's
status entry into an all-endpoint guarantee or add "only" to a nonexclusive rule.
Preserve explicit restrictions and exceptions when the source does state them.
This is a shared prompt instruction, not a word blacklist or an answer-repair step.

These instructions request behavior from the model; they do not guarantee it.
The citation validator checks bracketed source IDs, not semantic support. Source
review must still distinguish correct facts, unsupported additions, missing
citations, appropriate refusal and unjustified refusal.

The change addresses observed failures in the
[semantic acceptance review](../evals/library-runs/20260925T002400Z-semantic-acceptance/REVIEW.md).
[Offline checks](../evals/check-runs/20260925-generation-citations/README.md)
verify prompt delivery and source fidelity across complete and streaming paths.
The [frozen acceptance plan](../evals/library-runs/20260925-generation-citations/PLAN.md)
compares only generation with unchanged historical user/evidence messages and v11
assessments. All questions are development data, not independent release accuracy.

The [first fixed-context comparison](../evals/library-runs/20260925-generation-citations/README.md)
shows improved citation coverage on 22 valid paired reviews, with two assessment
timeouts. Several lists remain incompletely cited and a source qualification is
still overstated. Treat this as partial improvement; the change has not established
complete compliance or full-set release quality.

The [assessment-only supplement](../evals/library-runs/20260925-review-supplement-3/README.md)
keeps all original answers and failed attempts, reaches 23/24 valid reviews, and
records the remaining filename-metadata/source-line validation mismatch. The
[scoped retrieval probe](../evals/library-runs/20260925-parent-reranking/README.md)
uses this unchanged generation prompt; its manual point review is not v11 scoring.

The subsequent [source-scope instruction and fixed-context verification](../evals/library-runs/20260925-source-scope/README.md)
adds four lines requiring evidence-supported qualifiers and explicit restrictions.
All 68 scoped engineering checks pass, but only 3/5 selected live cases pass the
frozen review: the original scope concern is not clearly resolved, and one answer
misattributes an admissions-FAQ statement to the general FAQ. Both abstention
controls and the explicit-restriction control pass. The prompt change is not a
verified semantic fix; both this failure and the earlier 7/8 service run remain
unchanged. There was no new ingestion/retrieval or full benchmark in this replay.

The preceding [correction-session report](../evals/library-runs/20260925-grounding-high/README.md)
records named-document attribution rules, literal table-status handling, instruction
placement and optional answer reasoning configuration. Full backend checks pass,
but no tested configuration passes every frozen semantic gate. Current GPT-4.1
reaches 3/5; GPT-5.4-mini low/high reach 4/5 with different remaining failures.
The high-effort sample has supported claims/citations but omits reference details
and includes one non-English word. These observations do not justify claiming a
completed grounding fix or switching defaults. All previous failures and a labeled
reviewer correction remain intact; no generated response is repaired.

A subsequent [question-aligned correction](../evals/library-runs/20260925-answer-focus/PLAN.md)
separates requested answer points from optional adjacent facts. The awards rubric
previously demanded job competition/posting details that the question did not ask
for; its old scores remain intact. The prompt now requests a concise answer per
part, avoids repeated summaries and unrequested background, and explicitly applies
English to uncertainty/status labels. It still preserves needed qualifications,
source names and identifiers. This is a prompt constraint, not guaranteed language
or semantic validation. The [bounded default-model verification](../evals/library-runs/20260925-answer-focus/README.md)
passes 4/5: all requested facts and factual citations are supported, but the awards
answer still blends documents without identifying the other FAQ. No non-English
output was observed in this five-case sample. This is not full acceptance.


## Document selection and representation

The [document-scope implementation](document-scope.md) now enforces recognized
file restrictions before ranking and carries identity labels into budgeted source
metadata. Explicit multi-file requests select representatives before additional
same-file hits. The [completed comparison](../evals/library-runs/20260925-document-representation/README.md)
shows correct General-versus-Admissions attribution and 100% annotated comparison
evidence coverage, up from 50% before the representation correction.

This fixes the observed source attribution defect, but does not establish complete
acceptance: the comparison omits its frozen explicit General-FAQ absence point,
and the first pass retains a stream timeout and two slow completed generations.
One bounded recovery passes separately. Combined strict case coverage is 10/11,
service completion 11/12 attempts. Original answers, criteria, failures and missing
failed-request usage remain visible; no prompt/model retuning or merge followed.


The subsequent [awake-host acceptance](../evals/library-runs/20260926-comparison-awake/README.md)
passes all 11 unchanged strict cases, including both comparison points, and the
original latency gates. Host power logs explain a confound in the previous timing
sample; old failures remain unchanged. The generation format now explicitly
preserves one item per compared document. The new report retains a non-fatal
stream-finalizer warning and wording limitations; success supports the default
path's merge recommendation, subject to explicit user approval.
