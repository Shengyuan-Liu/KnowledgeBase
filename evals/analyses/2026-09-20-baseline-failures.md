# Baseline failure audit: September 20, 2026

## Scope and evidence

This is a Codex qualitative audit of the nine cases marked failed in the latest
LLM review of run `20260920T165211Z-da6c23f3`. It is not a human grading session,
a new evaluation run, or a revised score. The original **16/25 strict passes**
remain the recorded LLM result. The other 16 cases were not re-audited here.

Inputs: [baseline notes](../runs/20260920T165211Z-da6c23f3/README.md),
[final report](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md),
[original answers](../runs/20260920T165211Z-da6c23f3/answers.jsonl),
[reference cases](../runs/20260920T165211Z-da6c23f3/cases.json), and
[review history](../runs/20260920T165211Z-da6c23f3/reviews.jsonl).
All 45 retrieved excerpts and the reference spans for these nine cases were checked
against the frozen corpus at their recorded character offsets. They match.
These are observations about that frozen corpus, not refreshed NYU policy advice.

The baseline used 256-character chunks, 64-character overlap, top-k 5,
`text-embedding-3-small`, and `gpt-4.1-nano`. Its generation commit was `0493949b`;
the final judge used `gpt-4.1-mini`. No answers or historical ratings were changed.

## Findings

All nine failed cases have at least one required fact absent from the retrieved
context. This was established by reading the passages, not inferred only from
recall metrics. Five have zero annotated character coverage; four have partial
coverage. Some also show unsupported generation or omitted facts that were
available. These causes overlap and must not be counted as disjoint categories.

Several judge explanations incorrectly describe reference evidence as retrieved
evidence. Some also treat an omitted expected point as an unsupported claim.
Completeness, grounding, and citation support need separate judgments. Consequently,
the recorded scores are useful for locating candidates for inspection, but their
explanations are not authoritative diagnoses.

| Failed case | Annotated character coverage | Evidence-backed diagnosis |
| --- | ---: | --- |
| `policy-scope` | 0% | The scope sentence is absent; answer omits geographic and student-level coverage |
| `policy-off-campus` | 0% | Relevant section heading is retrieved without the operative rule; unrelated discretion language is misapplied |
| `msds-credits` | 0% | Five FAQ chunks replace curriculum evidence; answer invents a 30-credit requirement |
| `msds-industry` | 33.33% | Alternate bulletin supplies DS-GA 1009 and 3 credits, but the elective table is cut off; answer also omits the available 3-credit detail |
| `msds-online` | 0% | The direct FAQ answer is absent; model declines to confirm, while the judge incorrectly says the answer was retrieved |
| `msds-admissions-prerequisites` | 0% | Introductory/background text and referral links replace the actual prerequisite list |
| `msds-gre-submission` | 69.79% | Upload instruction is cut mid-sentence before destination and official-score instructions |
| `msds-tracks-change` | 50% | Change deadline is retrieved, track names are absent; answer promotes a concentration to a primary track |
| `msds-working-enrollment` | 19.81% | Working-student credit recommendation and summer rule are absent; full-time program load is substituted |

Coverage values are copied from the original records and rounded here. Matching an
alternative passage can be valid even when annotated coverage is low, as the
Industry Concentration case illustrates.

## Case-by-case review

Source numbers below refer to **that answer's retrieved sources**, not the gold
reference list. Offsets are half-open character ranges in the frozen TXT files.

### policy-scope

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#policy-scope).
The needed policy sentence is at `1591:1827`. None of the five chunks intersects
it. Source [2] discusses enforcement; [3] discusses organization responsibility.
They cannot supply all schools/locations, Study Away Sites, and Portal Campuses.

The answer is incomplete. The judge's explanation additionally mentions location
coverage from source [1], but that chunk (`576:832`) contains the document heading
and start of a statement, not the coverage sentence. This is a retrieval miss,
not evidence that the model ignored a complete scope statement in context.

### policy-off-campus

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#policy-off-campus).
Source [1] (`12288:12544`) reaches the section heading and beginning of a sentence.
The operative rule at `12837:13125` is absent. Source [3] (`14976:15232`) concerns
individuals and organizations and university discretion; it does not state a rule
about off-campus conduct.

The answer's attribution of off-campus authority to [3] is unsupported. It also
omits both substantial disruption and threats to health/safety/security. The judge
gives the first composite point full credit even though its disruption condition
is missing, and incorrectly treats [3] as evidence for off-campus authority.

### msds-credits

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-credits).
All five sources come from the general FAQ. The 36-credit sentence at curriculum
`424:494`, sample plan at `4557:5227`, and planning caveat at `4426:4555` are absent.
Source [1] discusses six independent-study credits, not a 30-credit degree.

The 30-credit answer is unsupported and wrong against the frozen reference.
The lack of semester details reflects missing context. The judge correctly flags
the wrong total but incorrectly claims the curriculum and plan were retrieved.
Improving retrieval and preventing unsupported totals are distinct problems.

### msds-industry

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-industry).
Source [2] supplies the mandatory first-year internship. Source [4], an alternate
bulletin passage at `4224:4480`, supplies DS-GA 1009, first-year timing, and 3 credits.
It ends at `Select two el`, before the elective areas and six-credit total.
Source [5] concerns the allowance for taking an elective pass/fail, not the two
required concentration electives.

The answer omits the available 3-credit detail and lacks the elective subjects and
total. Its citation [5] does not support the two-elective requirement. The judge
claims that [4] supplies the missing Big Data/NLP detail, says no citation was
provided for electives despite [5], and grants full credit to the first point
without the required credit count. The low annotated recall alone understates the
useful alternate evidence for DS-GA 1009.

### msds-online

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-online).
The direct answer is at admissions FAQ `777:845`; that file does not appear among
the five sources. The actual excerpts concern electives and the curriculum.
The model declines to confirm online availability, although its wording is poor.

It fails the answerable question, but abstaining when the retrieved evidence lacks
the answer is preferable to inventing one. The judge's claim that source [1]
explicitly contains the direct answer is false. Its grounding/citation zeros need
reconsideration separately from the correctness failure; this audit does not assign
replacement numerical scores.

### msds-admissions-prerequisites

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-admissions-prerequisites).
Source [1] (`1536:1792`) gives the heading and examples of undergraduate backgrounds.
The actual required subjects and Python/R expectation at `2266:2848` are absent.
Source [5] refers readers to the admission page and starts a separate question
about languages used in courses; it is cut at `Programming languages are decided by`.

The answer misses all four required points and conflates applicant backgrounds
with prerequisites. The judge is right about missing details, but its blanket
assertion that factual claims have no retrieved support is too broad: the listed
undergraduate backgrounds do occur in [1]. The course-language answer also goes
beyond the complete text actually available in [5].

### msds-gre-submission

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-gre-submission).
Sources [1] and [4] establish that the GRE is optional. Source [3] (`3648:3904`)
ends after the beginning of the unofficial-score PDF instruction. The destination
and requirement to also send official scores occur later in `3775:4101`.

The answer reproduces the part it received but cannot supply the cut-off details.
The judge claims the official-score requirement is in [3] and [4]; it is in neither.
Omission establishes incompleteness, not automatically lack of grounding. Citation
placement can still be improved: the optional-test statement is not directly cited,
while [3] supports the PDF statement. This is a concrete context-boundary case.

### msds-tracks-change

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-tracks-change).
Source [5] (`768:1024`) includes the end-of-second-semester deadline and Data Science
Track heading. The two-track list at `415:580` is absent. Other retrieved FAQ
passages mention the Industry Concentration, but not as a primary track.

The answer incorrectly names Industry Concentration as a track and attributes it
to [5]. The deadline is correct. The judge incorrectly says [5] explicitly names
both actual tracks. The problem combines missing track-definition context with an
unsupported substitution; the deadline demonstrates that useful evidence was used.

### msds-working-enrollment

[Recorded case](../runs/20260920T165211Z-da6c23f3/reports/20260920T165623Z-83a61c3d.md#msds-working-enrollment).
Retrieved admissions FAQ chunks describe the full-time load and lack of guaranteed
evening classes. They omit the six-or-fewer-credit recommendation for full-time
workers. The general FAQ's continuous-enrollment rule (`1582:1841`) is not retrieved
at all. Source [5] (`5760:6016`) describes a four-semester plan, not an enrollment rule.

The answer substitutes the full-time program load for the worker recommendation
and infers enrollment requirements from the sample schedule. The judge incorrectly
locates the six-credit recommendation in source [1] and gives the summer point full
credit despite the answer's qualified speculation. This needs retrieval and
answer-grounding attention, not just adding another sentence to the prompt.

## Next experiment, not yet executed

1. Freeze the current implementation and run a fresh 256-character baseline. The
   historical run predates the service/API changes and is not a paired control for
   a new code revision.
2. On the same commit, run a 512-character candidate with overlap 64, top-k 5, the
   same corpus/questions, and the same models. Change only the chunk-size setting.
   Larger chunks also increase the possible context budget and change stride; do
   not attribute any result exclusively to semantic boundary handling.
3. First compare retrieved passages, annotated character coverage, full evidence
   recall, and actual missing answer points. Prioritize GRE submission, industry,
   working enrollment, tracks, credits, and online availability for inspection.
4. Test the hypothesis: larger chunks preserve more adjacent instructions and
   entity context. It may still fail where ranking selects the wrong section or
   document. Do not assume the candidate improves quality before running it.
5. Keep the existing judge protocol for a mechanically comparable score, but
   separately inspect its disputed attributions. Calibrate a future judge protocol
   against clearly separated reference and retrieved evidence; a protocol change
   starts a new scoring series, not an apparent system improvement.

No reranker, hybrid search, prompt repair, or production retrieval change is
justified by this audit alone. Select later changes from the paired experiment's
remaining failures. New paid evaluation runs were not performed for this audit.
