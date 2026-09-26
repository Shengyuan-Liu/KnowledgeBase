# Source-grounded inspection

Reviewer: Codex. This is model-assisted inspection of actual saved answers and
supplied excerpts, not independent human grading. It does not rewrite the frozen
v11 scores or annotations. All statements below concern the frozen corpus, not
current university policy or live product documentation.

## Six newly frozen questions

Both strategies were inspected for each question: twelve answer instances. The
source IDs below refer to each answer's own `sources` array. Full answers, exact
source text and offsets remain in the two `answers.jsonl` files.

| Case | Parent-child / semantic evidence | Inspection |
| --- | --- | --- |
| `release-temperature` | Source 1 / 1, Anthropic parameter table | Both correctly state 0.0–2.0. The control also correctly states full support. Inline citation supports the fact. |
| `release-tool-definition` | Source 1 / 1, tools definition table | Both list name, input_schema and description as fully supported and cache_control as ignored. Citations appear after the list, so substantive support does not imply complete claim-local citation coverage under v11. |
| `release-research-fair` | Source 1 / 1, Summer Research Initiative paragraph | Both correctly state each spring and exclude students outside the CDS MSDS program. Both parts have citations. |
| `release-capstone-team` | Source 1 / 1, capstone overview | Both correctly retain “typically” and 2–4 people, with supporting inline citation. |
| `release-elective-approval` | Source 1 plus corroborating 2 / source 2, curriculum and general FAQ | Both give the Google form and all four requested items, including optional course website. Semantic additionally names the contact address present in its source 2. Citations after a list or a following paragraph do not cover every preceding claim under the frozen citation-locality rule. |
| `release-personal-capstone` | Saved capstone overview and other supplied general program excerpts | Both decline to invent a personal assignment or teammates. Suggested places to ask are general next steps, not documented assignment information. Citations must not be interpreted as proof that a specific portal or coordinator actually holds this user's assignment. |

The requested substantive facts are present in the five answerable cases in both
modes; both refuse to invent the unanswerable personal assignment. This small,
Codex-authored sample on familiar documents does not establish general accuracy,
independent holdout performance, or perfect citation behavior.

## Confirmed evidence and answer regressions

### `msds-working-enrollment`

The control supplies the admissions FAQ and general FAQ. It answers all three
parts: at most six credits for full-time workers, no guaranteed evening courses,
and continuous enrollment in fall/spring but not summer.

Semantic selects five children from the admissions FAQ and ultimately supplies
only that document's first parent. Its candidate pool partially contains the
second gold region, but the selected five children and supplied evidence cover
only the first region (gold-span character coverage 1.00 → 0.50). The answer
correctly handles workload and evenings but explicitly declines to answer the
summer part. This is a retrieval-caused incomplete answer, not an invented summer
rule or a refusal despite adequate supplied evidence. The control's source 2
contains the missing sentence: “This requirement does not apply to the summer
semester.”

### `msds-cpt-source-context`

The control supplies both descriptions, attributes them to their respective
pages, and preserves the timing difference. Semantic's candidate pool misses the
admissions FAQ gold span about paid CPT internships after the first year. Parent
expansion restores the Industry Concentration statement about a mandatory
internship within the first year and early-CPT advice, but cannot recover the
missing FAQ span (final character coverage 1.00 → 0.50).

The semantic answer correctly presents the supplied concentration information and
says the admissions excerpt lacks timing information. It therefore fails the
requested two-source comparison. The missing FAQ statement is in the corpus but
absent from the supplied evidence; this is not grounds to penalize the model for
refusing to invent it. Candidate, selected-child and packed-evidence traces
distinguish this loss from an evidence-budget exclusion.

## Formatting-sensitive coverage

Both modes miss only blank-line separator characters in five DeepSeek gold
regions: `api-setup`, `api-model-mapping`, `api-top-p`, `api-thinking` and
`api-tools`. The [collection audit](collection-audit.json) retains exact uncovered
offsets and characters. No substantive gold text is missing for these five cases.
The frozen full-span metric remains unchanged, including its penalties; it must
not be interpreted as a count of wholly unsupported answers. This differs from
the two material source omissions above.

## Judge caveats observed during inspection

- In the control's `msds-credits`, v11 treats the answer's self-description of
  covering all requested parts as an unsupported source claim. This is a disputed
  inventory choice: a meta-comment about the answer is not an external source
  fact. The original penalty remains in the results.
- Claim-local citation coverage is stricter than a reader's interpretation of a
  citation after a paragraph or bullet list. Correct source IDs and available
  supporting text do not eliminate this recorded placement failure.

### `api-thinking`: stronger behavior than the evidence states

The semantic answer describes other `output_config` values as ignored. Its source
table states only that `effort` is supported. Unsupported fields might be ignored,
rejected or handled differently; the supplied table does not resolve this. The
judge records a faithfulness regression even though the requested expected points
remain correct. This is a supported reason to keep expected-point correctness
separate from the faithfulness of additional claims.

### `release-personal-capstone`: advice and citation placement

The semantic answer's first paragraph correctly refuses the personal assignment
and summarizes the general excerpts, but has no local citation. Its second
paragraph recommends another source and names official communications, a course
portal or a coordinator, then cites `[1] [4]`. Those excerpts do not name those
channels. V11 marks both the need to consult elsewhere and the listed channels
as unsupported, producing faithfulness 0.60 versus control 0.75 and citation
coverage 0 versus 0.75. Both answers still abstain appropriately on the actual
personal-assignment request. Treating the necessary next-step advice itself as
an external source claim is a disputed inventory choice; citing specific channels
as if the corpus documents them remains a real support limitation. All original
assessments remain unchanged.

These are all cases with paired decreases in expected-point correctness or
faithfulness: working enrollment, CPT source context, API thinking and personal
capstone. Exact source coverage has only the first two material regressions.

The control also has representative unsupported additions: the personal-schedule
answer extends a course-description reference to schedules, and the admissions
answer adds claims about addressing prerequisite gaps and electives not replacing
prerequisites. The new elective answer's “appropriate program administrator” is
an imprecise generalization of named contact guidance. Both personal-assignment
responses add generic places to ask, which are not evidence of the user's actual
assignment. Those assessments remain visible, including judgment calls about
whether advice should be classified as an external factual claim.

Additional claim-level findings and paired score changes are retained with the
final comparison; no answers or judge outputs were regenerated to improve scores.
