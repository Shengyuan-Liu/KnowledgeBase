# Judge v11 acceptance review

The contradictory refusal state is now excluded by the assessment output schema.
All 18 saved answers received valid judgments in this run, compared with 17/18 in
v10. This is an operational improvement, not proof of semantic correctness or
better RAG answers. The fixed calibration still has one verdict-subtype mismatch.
User acceptance and merge approval remain outstanding.

## Change and controls

Protocol `claim-inventory-v11` uses nested refusal variants with fixed boolean
combinations, answerability constraints, and required refusal evidence. Stored
assessment fields retain their previous meaning through shape conversion, without
repair, retries or score overrides. Prompt clarifications retain both halves of
contrast clauses and separate editorial emphasis from source-attributed facts.
See the [metric definitions](../../metrics.md) for the allowed states.

Both runs use `gpt-5.4-mini`, high reasoning, four workers, 180-second per-call
timeouts, and zero retries. There are three calls per completed review. The
16 calibration cases and labels are byte-identical to v10. The 18 real answers,
supplied evidence and original RAG measurements are also byte-identical to v10.
No ingestion, retrieval, generation or application-library mutation ran here.
The two new live batches ran sequentially. No warmup was performed; provider
load, caching and device are uncontrolled. Schema and prompts changed together.

## Measured comparison

| Metric | v10 | v11 |
| --- | ---: | ---: |
| Calibration valid reviews | 15/16 | 16/16 |
| Calibration strict label agreement | 15/16 | 15/16 |
| Correct calibration answers matching labels | 10/10 | 10/10 |
| Known errors detected with valid negative reviews | 4/5, one pending | 5/5 |
| Appropriate calibration refusal | 1/1 | 1/1 |
| Calibration judge mean / P50 / P95, seconds | 12.575 / 10.236 / 23.846 | 14.170 / 12.182 / 28.080 |
| Calibration API calls | 48 | 48 |
| Calibration input / output tokens | 75,590 / 32,400 | 81,862 / 31,025 |
| Saved-answer valid reviews | 17/18 | 18/18 |
| Saved-answer judge mean / P50 / P95, seconds | 62.399 / 49.451 / 189.363 | 85.666 / 62.972 / 208.427 |
| Saved-answer API calls | 53 | 54 |
| Saved-answer input / output tokens | 238,315 / 239,316 | 261,316 / 245,088 |
| Saved-answer total tokens | 477,631 | 506,404 |
| API errors / timeouts / retries, each batch | 0 / 0 / 0 | 0 / 0 / 0 |

All timing distributions include completed attempts, including pending judgments;
P50 is the median and P95 is nearest rank. Worker queue wait is excluded. v11
saved-answer stage means are 17.202 seconds for extraction, 7.420 for audit and
61.037 for assessment (18 observations each). The complete batch took 417.102
seconds at concurrency four, or about 0.0432 valid reviews/second. Calibration
wall time was 70.224 seconds. These are evaluation timings, not RAG response
latency. Billed cost is unavailable, not zero. Single-pass latency differences
cannot be attributed solely to the code change.

The current 18-answer model assessments report expected-point correctness 98.15%,
faithfulness 98.30%, attempted-point completeness 100%, citation support 96.91%,
and citation coverage 62.39%. The strict pass rate is only 4/18 (22.22%): it also
requires all factual claims to be supported and cited under the same-line citation
rule. Valid grading therefore does not mean all answers passed. Claim splitting
changes denominators; do not interpret citation/faithfulness changes as RAG gains.
The previous full-set strict pass rate was unavailable due to a pending review.
Per-case scores, including regressions, are preserved in the comparison JSON.

Annotated character coverage remains 99.957% and full-span coverage 68.75%
(16 answerable cases), recomputed from the unchanged recorded evidence. RAG
response timing and generation usage are reused observations, not fresh measurements.
The linked summaries retain the full metric inventory, missing-data reasons,
retrieval relevance-label limitations, and separate quality/performance definitions.

## Targeted semantic review

Codex inspected original answers, source text, extracted claims and reasons; this
is not independent human labeling. No machine scores were changed.

- `personal-schedule-invented`: the old contradictory refusal flags are gone.
  Invented time/room claims are rejected, but classified as `contradicted` rather
  than the frozen expected `insufficient`. A source saying it does not list times
  is not evidence of a different time. This remains an error. `make eval-calibrate`
  intentionally exits nonzero (evaluator 1, Make 2).
- `msds-pathbreaker-fall2027`: the inventory now retains both encouragement and
  the explicit absence of a mandate. Audit passes, and both are supported.
- `msds-gpa`: editorial "main" emphasis is separated from the supported claim
  that the FAQ states the requirements. The previous negative verdict is absent.
- `msds-credits`: "other factors" remains an unsupported addition to the source's
  course-availability condition. Core facts are correct; the extra assertion
  should not be exempted merely to improve scores.
- `missing-personal-schedule`: the judge now rejects "recommended first-semester
  course" because the cited sample plan does not explicitly say "recommended".
  Whether this is a faithful paraphrase needs adjudication; it is a possible false
  negative. Appropriate refusal remains credited, but strict pass changes from
  true to false. This regression remains visible.
- `api-setup`: partial expected-point credit reflects an omitted
  `anthropic.Anthropic()` construction step in the frozen expected point. The
  question explicitly asks for the invocation method; the reference point is
  broader. Do not silently change the benchmark or label this as a generation
  regression: the answer bytes are unchanged.
- `api-thinking`: "only effort is supported" does not establish that other fields
  are ignored. The new insufficient verdict is defensible under the strict source
  rubric. The specific ignored `thinking.budget_tokens` field remains distinct
  from the parent object. This is a changed judgment, not a changed answer.

The semantic rubric is now held at v11 after one bounded pass. Do not tune until
this small set becomes green. Future comparisons should freeze this version and
explicitly flag disagreements; independent human adjudication is needed before
claiming general grader accuracy.

## Verification and records

- [Targeted checks](targeted-1.json): 44 passed.
- [Full backend checks](backend-1.json): 524 passed, 1 skipped; existing dependency
  deprecation warning. No live quality or provider costs are assigned to mocked tests.
- [Experiment plan](experiment-plan.json), [machine comparison](comparison.json),
  [all saved-answer inventories and negative verdicts](saved-answer-inspection.json),
  [targeted semantic review](semantic-review.json).
- Calibration [before](../../calibration-runs/20260924T193931Z-14f32e71-claim-inventory-v10/summary.json)
  and [after](../../calibration-runs/20260924T195838Z-1b2656db-claim-inventory-v11/summary.json).
- Saved-answer [before](../../calibration-runs/20260924T194004Z-1a80463c-saved-answers-high/summary.json)
  and [after](../../calibration-runs/20260924T200002Z-de0c50b4-saved-answers-high/summary.json).
- Console inventories: [calibration](calibration-console.log),
  [saved answers](saved-answers-console.log), [comparison](comparison-console.log).
- Reproduction: `make eval-calibrate`; saved-answer batch used the retained
  `regrade_saved_high.py` experiment script in the previous check directory;
  `compare.py` here compares the exact named runs and never changes their scores.
