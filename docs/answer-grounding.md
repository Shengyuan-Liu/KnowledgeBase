# Answer citations and source fidelity

The shared `ANSWER_INSTRUCTIONS` in `knowledgebase/rag/generation.py` governs both
complete and streaming answers. `_answer_messages` supplies the original question,
optional conversation interpretation and numbered evidence. `generate_answer`
and `stream_answer` send the same messages through their respective clients.

Factual claims should have a supporting citation in the same sentence or list
item. Each factual list item needs its own citation; an introduction, final bullet
or later summary does not implicitly cite earlier items. If different excerpts
support different claims, split the sentence or attach each citation to its claim.
Code examples use valid language comments beside source-derived lines so citations
do not alter literal values or executable syntax.

Answers must preserve the source's stated behavior and qualifications. A field
being unsupported does not establish whether it is ignored or rejected. Missing
personal information should be identified explicitly. Next steps and contacts
may be named only when the supplied evidence provides that guidance for the
requested information; a general program description does not document how to
find a particular student's assignment or schedule.

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
