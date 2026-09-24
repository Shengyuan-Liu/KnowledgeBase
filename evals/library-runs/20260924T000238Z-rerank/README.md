# Integrated reranking: paired library check

Run: 2026-09-24 UTC (2026-09-23 local). Development base: `15086cd`, with
the integration changes recorded by the working-diff hash in [run.json](run.json).
This is a small development comparison, not an independent acceptance decision.

## Setup

The 18 frozen questions are byte-identical to the
[previous hybrid run](../20260923T221737Z-hybrid/README.md): 16 answerable and two
unanswerable cases. The stored library is identical too: 17 Ready files, 38 parents,
and 92 children. No files were uploaded, deleted, or re-embedded for this run.
The previous run and annotations were not edited.

Both routes use BM25/vector candidate limits of 20, RRF k=60, child top-k=5,
and a 4096-token numbered evidence budget. The treatment scores the leading 20
fused children with `gpt-4.1` before selection and parent expansion; the control
uses RRF order directly. Generation uses `gpt-4.1`, embeddings use
`text-embedding-3-small`, and scoring has a 16384 message-text token limit.
The provider client uses a 90-second timeout and one SDK retry. Three workers
interleave both routes; these timings are not a single-user latency benchmark.

## Automatic measurements

| Measurement | Hybrid | Hybrid + rerank |
| --- | ---: | ---: |
| Successful answers | 18/18 | 18/18 |
| Mean annotated character coverage, 16 answerable cases | 93.707% | 99.957% |
| Full annotated span coverage, 16 answerable cases | 62.50% | 68.75% |
| Mean numbered evidence tokens | 2646.89 | 2537.94 |
| Mean total answer time | 2.86 s | 7.03 s |
| Mean scoring-stage time | 0 s | 4.52 s |

Coverage improved for the prerequisite case and was unchanged on every other
answerable case. The remaining five incomplete span matches are solely newline
separators omitted between exact structural regions; [audit.json](audit.json)
records every missing character and offset. These metrics measure supplied
evidence, not answer accuracy. Valid citation IDs also do not establish semantic
support.

All 36 answers passed source-fidelity and context-budget checks. All 360 scored
candidate IDs/texts matched the stored children; final child selection matched
rerank order, and source metadata retained the original RRF ranks separately.
Input-text counts ranged from 4389 to 10766 tokens per scoring call. This count
excludes schema, provider framing, and outputs. This run did not collect provider
usage totals or billed cost, and does not claim cost equivalence.

## Answer inspection and remaining issues

[reviews.jsonl](reviews.jsonl) contains one development review for each answer,
with reference-point checks, notes, issues, and source IDs. The reviewer was the
implementing Codex assistant; these are not blind or independent human grades.
No aggregate answer-accuracy score is reported.

- **Prerequisites:** the directly supporting child moved from RRF rank 5 to
  rerank rank 1. Hybrid excluded its admissions parent after FAQ parents consumed
  the budget. Reranking supplied the admissions parent first and generated the
  full subject list and Python/R expectations. Evidence coverage changed from
  0% to 100%, with 2774 final evidence tokens versus 3067 in the control.
- **Academic progress:** the factual child moved from rank 11 to rank 1. Both
  answers already covered GPA 3.0 and 66% credit completion, because the hybrid
  route reached that parent through a sibling. This is a ranking improvement,
  not a newly correct answer.
- **CPT:** both pages remain present, and both answers preserve their different
  timing statements. Both also infer a general-program/concentration distinction;
  the saved excerpts do not themselves resolve eligibility policy. Reranking
  does not remove this generation-level interpretation issue.
- **API setup:** the invocation-code child moved from rank 6 to rank 1, and its
  parent supplies the SDK, environment variables, constructor, and invocation.
  The reranked answer names `client.messages.create` but omits the explicit
  `client = anthropic.Anthropic()` statement, which the control includes. The
  third reference point is therefore marked partial for the reranked answer.
  Better ranking does not guarantee a more complete answer.
- **Unanswerable cases:** both routes decline to invent a personal class time
  or an exact tuition total. Related passages still receive nonzero relevance
  scores; abstention comes from generation, not a scoring threshold.
- **Selection:** low-relevance and even zero-score children can still fill the
  five selected slots. Siblings consume slots, parents can still be excluded,
  and tie-breaking retains RRF order. No threshold, backfill, question-specific
  tuning, or fallback was added to improve these results.

## Application and regression checks

The ignored local `.env` now enables reranking; the shared defaults and template
remain disabled so experiments can explicitly select either route. The built
frontend and API were restarted on `127.0.0.1:8000`.
[app-smoke.json](app-smoke.json) records a real streamed prerequisite answer and
a JSON follow-up using the same conversation. The resolved follow-up is passed
to reranking. The two saved exchanges retain identical source and ranking traces;
all five earlier conversations remain readable and all 17 library files are
unchanged. The follow-up repeats its answer in two sections, an existing answer
presentation limitation rather than a retrieval failure.

Offline verification: 471 backend tests passed, one opt-in live test skipped;
32 frontend tests, production build/type checking, and nine browser tests passed.
Tests include scoring before top-k, parent deduplication and whole-region budgets,
Ready-file filtering, separate ranks, API JSON/SSE, CLI/evaluation settings,
restart and deletion history, scoring errors, and disconnect during scoring.
Desktop/mobile browser flows verify visible ranks and historical evidence.

## Artifacts and reproduction

- [cases.json](cases.json): frozen questions, reference points, and spans.
- [chunks.json](chunks.json): exact stored file metadata, parents, and children.
- [answers.jsonl](answers.jsonl): all 36 answers, actual evidence, full retrieval
  and scoring traces, coverage, and durations.
- [summary.json](summary.json): automatic aggregates.
- [audit.json](audit.json): source/selection checks and remaining span gaps.
- [reviews.jsonl](reviews.jsonl): per-answer assistant inspection.
- [run_evaluation.py](run_evaluation.py): paired live runner.
- [run_smoke.py](run_smoke.py): live API/history check, which creates one conversation.

To repeat, copy the runner and frozen cases into a **new** run directory. Stop the
API before the paired runner opens the same data directory, then execute it with
`PYTHONPATH=. .venv/bin/python <new-run-dir>/run_evaluation.py` from the repository
root. It reads `.env`, makes paid calls, and refuses to overwrite artifacts.
Restart the app before running the smoke script. Repeated model outputs and
timings can differ; the recorded library must match for a comparable result.
