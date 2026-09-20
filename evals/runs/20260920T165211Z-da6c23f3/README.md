# First recorded baseline

This is one real API run of the existing system, followed by LLM grading. It is a
development baseline, not evidence of improvement or a held-out accuracy estimate.

- [Final detailed report](reports/20260920T165623Z-83a61c3d.md)
- [Machine-readable final snapshot](reports/20260920T165623Z-83a61c3d.json)
- [Questions and reference evidence](cases.json)
- [Original answers and retrieved sources](answers.jsonl)
- [All review attempts, exact prompts, and raw judge responses](reviews.jsonl)
- [Run configuration and code provenance](run.json)

## Configuration and observations

Generation used code commit `0493949b602055249d0099c433dc4d466e88861a` with a clean
working tree, `gpt-4.1-nano`, `text-embedding-3-small`, 256-character chunks,
64-character overlap, cosine distance, and top-k 5. All 16 corpus documents were
freshly indexed. All 25 questions completed without generation errors.

The final judge was `gpt-4.1-mini`, reviewer ID `gpt-4.1-mini-v1`. The second grading
round used evaluator commit `9f6348a`; the exact full commit and implementation
hashes are in each of those review records. Its dirty flag reflects the untracked
run artifacts at grading time. No manual scores were substituted for LLM scores.

| Metric | Observed result | Scope |
| --- | --- | --- |
| Strict pass rate | 16/25 (64%) | Latest LLM judgments; all applicable criteria must receive full credit |
| Answer-point score | 77.67/100 | Macro average across all 25 graded questions; not overall accuracy |
| Answerable strict passes | 11/20 (55%) | Latest LLM judgments |
| Unanswerable strict passes | 5/5 | Only five development questions; not a broad refusal guarantee |
| Annotated character recall | 53.35% | 20 successful answerable cases; span-union coverage, not semantic relevance |
| Full evidence recall | 44.17% | Same 20 cases; alternative unannotated evidence can be valid |
| Question latency P50 / P95 | 1.236 / 1.886 seconds | 25 successful calls; includes evaluation offset lookup, excludes ingestion and judging |

## Concrete failure and judge limitations

For `msds-credits`, the system retrieved five FAQ excerpts instead of the annotated
curriculum evidence and answered that the degree requires **30 credits**. The gold
reference says **36 credits**. Annotated evidence coverage is zero for this question.
This is a traceable retrieval miss plus an unsupported answer, suitable for a future
chunking/retrieval experiment. The baseline alone does not establish which change
will fix it.

The first grading round produced two invalid reviews (`msds-credits` and
`msds-online`) because the judge assigned abstention scores to answerable questions.
They remain in the log. The evaluator was updated with explicit per-case schema
constraints and clearer evidence boundaries, then all 25 saved answers were graded
again without regenerating answers. The second round produced 25 valid reviews.
The log therefore contains 50 review attempts; the final report uses the latest 25.
This judge-protocol change is not a system-quality improvement.

Schema validity does not establish judgment quality. A spot check of the second
`msds-credits` review found that its explanation still called gold curriculum
passages "retrieved," although those passages are absent from `answer.sources`.
The incorrect 30-credit answer is independently visible in the raw record, but
the judge's explanation should not be treated as authoritative error attribution.
Human calibration of all cases has not been completed. Retain this limitation when
using these scores, and review disputed grounding/citation ratings before making
resume claims.

For future comparisons, keep the same frozen inputs and judge protocol, change one
system factor, and use the [evaluation workflow](../../README.md). Preserve both
improvements and regressions, and repeat promising results to assess variability.
