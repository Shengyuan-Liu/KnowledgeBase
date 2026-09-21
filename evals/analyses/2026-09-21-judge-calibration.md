# Judge evidence validation and paired regrading

## Outcome

The evaluator now requires auditable answer/source evidence, uses a strict response
schema, and derives aggregate scores from individual assessments. Regrading the
same 50 answers exposed failures in the existing `gpt-4.1-mini` judge: **27 reviews
passed structural/evidence checks and 23 remain pending**. A checked review is not
necessarily semantically correct. Neither run has a reportable full pass rate,
and the comparison deliberately suppresses score deltas.

This fixes acceptance of several mechanically detectable judge mistakes. It does
**not** establish a calibrated, trustworthy quality judge. Application generation,
retrieval, chunk defaults, original answers and historical reviews are unchanged.
No human ratings were created and no invalid reviews were repaired or selectively
retried to obtain a preferred score.

## Implementation and verification

- `fcc3290` introduced point evidence, claim evidence, quote validation, deterministic
  abstention mapping and report rendering. Human imports and historical ratings
  retain their existing format.
- `8f183ad` constrained API output using strict JSON Schema after observed format
  failures in the initial live attempt. Only the evaluator uses this response
  constraint; the application answer model and client are unchanged.
- The final full offline suite passed: **244 tests passed, 1 live test skipped**.
  Tests cover invented waiver answer quotes, gold-only online text incorrectly
  attributed to retrieval, the GPA sentence-end citation, abstention mapping,
  invalid evidence retained as pending, strict API schema requests, historical
  review preservation and rejection of mixed-protocol comparisons.
- These offline cases test validation/aggregation with controlled judge outputs.
  They do not prove that a real model classifies the examples correctly. The live
  findings below are the separate behavioral check.

The protocol supplies expected points and scoring notes for correctness, but omits
gold excerpts, prior ratings and retrieval metrics from the judge's input. It asks
for exact answer quotes for point credit, and actual source IDs/quotes for factual
support. It computes grounding/citation scores from the claim assessments and maps
abstention categories to null/0/1/2, avoiding an independently generated refusal score.

Quote validation establishes provenance, not entailment. The judge may still choose
an irrelevant real quote, omit factual claims, over-credit a composite point, or
misclassify a personal-status inference. In particular, an empty claim list cannot
by itself prove that an answer makes no factual assertions. The live results show
that limitation; aggregate quality comparisons must remain blocked.

## Live grading history

Both runs retain their original 25 reviews. Protocol 2 was stopped after repeated
schema errors (mostly an extra legacy `issues` field); 15 control and 14 candidate
responses were recorded, none valid. Those **29 failed attempts** and their
intermediate reports remain available. In-flight interrupted responses are not
counted as completed reviews. There was no selective retry under that protocol.

Protocol 3 then graded **all 25 saved answers in each arm once**, with the same judge
model/reviewer as before: `gpt-4.1-mini` / `gpt-4.1-mini-v1`. Both used evaluator
commit `8f183ad`, identical implementation hashes and protocol hash
`a92654e9b75e02db2e5acec3d06ec0a09669a60638e17a162dd2e55cc00d5fc9`.
The dirty checkout at grading time contained the retained prior review artifacts;
the evaluator code matched that commit. The scoring rubric remains version 1;
the judge protocol changed, so old/new scores are not an application improvement.

| Run | Protocol 3 attempts | Checks passed | Pending | Full pass rate |
| --- | ---: | ---: | ---: | --- |
| [256 control](../runs/20260920T235448Z-2d9f6276/README.md) | 25 | 14 | 11 | Unavailable |
| [512 candidate](../runs/20260920T235545Z-199abacb/README.md) | 25 | 13 | 12 | Unavailable |

- [Control protocol 3 report](../runs/20260920T235448Z-2d9f6276/reports/20260921T001453Z-be4922ab.md)
- [Candidate protocol 3 report](../runs/20260920T235545Z-199abacb/reports/20260921T001521Z-49652a54.md)
- [Comparison with suppressed deltas](../comparisons/20260921T001557Z-e17ab8a6.json)
- [Original paired experiment](2026-09-20-chunk-size-256-vs-512.md)

All 50 protocol 3 responses parsed and matched the schema. Of the 23 rejected
reviews, 22 used a quote absent from its declared answer/source; one awarded factual
grounding without source evidence. Some quote mismatches are paraphrases or whitespace
changes rather than invented facts. They are still invalid under the exact-quote
contract, not automatically wrong answers. Unreviewed cases are never scored zero.
Report answer-point means describe only the checked subset and must not be compared
as full-set scores.

## Regression inspection

The observations below are Codex qualitative inspection, not human calibration or
replacement grades. The raw responses can be found by case ID in each run's
`reviews.jsonl`; the new protocol version identifies the relevant records.

| Observed problem | Protocol 3 result | Interpretation |
| --- | --- | --- |
| Candidate waiver received credit for omitted submission instructions | Judge again copied instructions into purported answer quotes; rejected | Invented answer evidence no longer becomes a valid score |
| Gold online-availability answer treated as retrieved/answered | Both judges put the gold answer into answer quotes despite the refusal; rejected | Reference-to-answer leakage is detected even for a zero-scored point |
| Control GPA had a valid single sentence-end citation | Judge paraphrased the credit-completion clause as an exact quote; rejected | Offline citation regression passes, but this live review remains unresolved |
| Control GRE omitted the official-score instruction | New point scores `[2, 2, 0]` detect the third omission | Second point is still over-credited: the upload destination is absent; exact quotes alone do not ensure complete point coverage |
| Candidate personal capstone refusal received abstention 0 | Classified as explicit missing information; derived abstention 2 | This particular classification improved |
| Control capstone incorrectly asserted no assignment had happened | Still classified as explicit missing information and passed quote checks | Unsupported personal-status inference remains a semantic judge error; its empty claim list hides the assertion |
| Candidate tuition invented a $0 bill | Review rejected due to a nonmatching source quote | Its raw refusal category still conflicts with its reason, which acknowledges invention; semantic refusal classification is not solved |

Other checked reviews also omit claim assessments for factual answers. The control
degree-credit review gives full credit to the course-availability caveat despite
its absence. These are reasons to distrust even the 27 checked ratings, not reasons
to repair scores manually or relax evidence checks until the run becomes complete.

## Artifact integrity and next decision

Original `answers.jsonl`, `cases.json`, `corpus.json`, and `run.json` match the
pre-regrading Git versions byte for byte. Both review logs preserve their original
byte prefixes and append the protocol 2/3 attempts. Earlier reports and the original
comparison are retained. New reports normalize only Markdown display whitespace;
exact responses and source text remain in JSON/JSONL. Local links, JSON parsing,
review counts, protocol hashes, answer hashes and staged whitespace were verified.

Keep the current application configuration. Before further chunk-size selection,
use the already observed disagreements to build a small independently reviewed
calibration set, then evaluate a stronger judge or a simpler separated point/claim
assessment protocol against it. Any later regrade should cover both full answer sets
under a single protocol and preserve this attempt. Do not present these results as
human validation or a reliable new RAG pass rate.
