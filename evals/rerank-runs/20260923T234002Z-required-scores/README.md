# Required-Score Reranker Probe

The standalone `child-relevance-v2` reranker scored the same four development
questions and RRF top-20 windows from the
[hybrid comparison](../../library-runs/20260923T221737Z-hybrid/README.md).
It uses the existing `.env` provider and `gpt-4.1` configuration. No retrieval,
parent packing, answer generation, upload, or conversation write occurred.

All four requests returned all 20 scores: 80 scored children in total. The output
schema requires an integer score for every candidate ID, correcting the observed
[19-of-20 omission](../20260923T233640Z-standalone/README.md). A successful probe
does not prove that every future request or provider will succeed.

## Candidate movements

| Question / relevant child | RRF rank | Rerank rank | Score |
| --- | ---: | ---: | ---: |
| Admissions prerequisites: actual calculus, linear algebra, CS, and programming requirements | 5 | 1 | 3 |
| GPA: explicit 3.0 and 66% requirements | 11 | 1 | 3 |
| CPT: Industry Concentration timing | 1 | 1 | 3 |
| CPT: admissions FAQ timing | 2 | 2 | 2 |
| API setup: Python constructor and invocation code | 6 | 2 | 3 |
| API setup: environment-variable code block | 8 | 3 | 3 |

The prerequisite child belongs to the same 1312-token parent that hybrid retrieval
previously excluded after two FAQ parents consumed the budget. Moving that child
first is promising for the planned integration, but this probe did not expand
parents or generate a new answer and therefore does not establish an end-to-end fix.
Likewise, improving the GPA child rank is not proof of better final evidence:
the earlier hybrid pipeline already supplied its parent through a sibling hit.

## Latency, usage, and limits

Measured scoring durations were 4.01, 3.92, 5.61, and 3.21 seconds (mean 4.19 s).
These are four sequential development calls, not a latency distribution or a
comparison with a local cross-encoder. They measure an additional ranking step;
integrated chat latency has not been measured.

Provider-reported usage totals 38,078 input tokens and 2,223 output tokens for
these four requests. Actual billing was not read or estimated. Exact usage per
request is retained. The local message-text budget excludes the schema and API
framing, so its counts are smaller than the provider's input-token counts.

Scores are coarse model judgments, not ground-truth relevance labels. The model
still gives score 3 to the API guide's short "Config Environment Variables" step
heading. It also gives score 3 to a less directly relevant general-FAQ child in
the GPA question. Thus, rankings are not perfect even when the identity/schema
contract succeeds. No question-specific boost or prompt tuning on expected answer
points was added; the schema correction addresses completeness only.

This is a four-case targeted check, not the full 18-question acceptance suite.
It cannot establish aggregate answer accuracy, budget behavior, cost-effectiveness,
or the best model choice. Those remain integration-stage work.

## Artifacts

- [run.json](run.json): resolved model/configuration, base revision, and input hashes.
- [results.jsonl](results.jsonl): full scored candidates, exact messages, original
  route/RRF scores, new scores/ranks, raw provider outputs, usage, and duration.
- [summary.json](summary.json): target-ID rank movements and per-call usage.
- [run_evaluation.py](run_evaluation.py): reproduction procedure using the existing
  `.env`. Copy this runner into a fresh output directory and run from the repository
  root with `PYTHONPATH=.`; it protects existing artifacts with exclusive-create writes.

The implementation and schema fix are included in the commit containing this report;
the recorded base revision predates these uncommitted changes. The active chat
path remains hybrid RRF until the standalone module is explicitly integrated.
