# Judge calibration development record

All development was performed on `v1`, based on `76db4b5`, without merging to
`main`. Existing answers, source offsets, corpus, retrieval configuration and
generation settings were preserved. Only grading calls were made for saved-answer
experiments. Credentials stayed in ignored `.env`.

## Changes

- Protocol 10 retains logical alternatives, conditions and restrictive qualifiers.
- A separate source-blind inventory audit receives only answer units and extracted
  assertions, before the evidence assessment. Source facts cannot be confused with
  extraction fidelity in that call.
- Conjunctions can be split into jointly asserted facts; disjunctions cannot become
  individually required facts. Documented procedures remain factual assertions.
- Nonexhaustive paraphrases and editorial emphasis have an explicit rubric;
  explicit policy priority and exclusivity remain factual.
- `make eval-calibrate` reports fixed-label agreement, rejected correct answers,
  detected errors, refusals, pending judgments, latency, usage and reliability.
- Calibration distinguishes detecting a wrong answer from correctly classifying
  its error as contradicted versus insufficient.

## Preserved experiments

Every run contains its original prompts, schemas, input snapshots, model settings,
raw responses, judgments, usage and timing. Original results remain unchanged.
`summary-audited.json` and `checks-audited.json` append reporting corrections:
judge timing points to `reviews.jsonl`, and a wrong negative verdict subtype is
not mislabeled as accepting an incorrect answer. It still fails strict calibration
agreement. No semantic score was manually repaired.

Two fixture issues were discovered and recorded before using final results:

1. [Necessary versus sufficient condition](label-correction.json): the first
   positive qualifier fixture incorrectly assumed that a necessary condition was
   sufficient. Both positive/negative source excerpts now state a biconditional.
2. [FAQ identity](source-identity-correction.json): a synthetic answer named a FAQ
   but its supplied source had no FAQ identity. The final fixture supplies that
   identity explicitly; source support for the attribution can now be evaluated.

[Two additional regressions](dataset-extension.json) cover nonexhaustive lists and
editorial summaries. The original 12 corrected cases remain identical except for
dataset-version metadata, allowing a matched comparison; the two new cases are
reported separately from that baseline. Two final regressions cover answer source
lead-ins and nested-field summaries; the final set has 16 cases. Labels are authored
by Codex, not a human.

Protocol 4 is replayed from [the original code](judge-v4.py). Protocols 5 and 6 were
tested during development; their complete sources are retained in each calibration
run. [Protocol 7](judge-v7-candidate.py) and [protocol 8](judge-v8-candidate.py)
preserve intermediate candidates. Protocol 9 was tested at both medium and high
reasoning. [Protocol 9](judge-v9.py) also exposes semantic source-attribution and
nested-field interpretation failures on real answers, despite passing its 14 small
high-effort fixtures. Protocol 10 adds those two regression classes and is evaluated
on the 16-case set and all 18 real answers. No retry/repair loops were added, and
failed attempts were retained. A small passing set never establishes general truth.

The two `make eval --answers-from ...` invocations regraded the same saved answers
twice because their automatic comparison regraded the previous run too. Those
paired results describe judge variation, not RAG changes. The final high-effort
[saved-answer runner](regrade_saved_high.py) grades the 18 saved answers once,
using production judge/orchestration helpers. It avoids another duplicate grading
of byte-identical answers. It was run separately for protocols 9 and 10. The isolated RAG ingestion/generation pipeline was not
rerun in this task.

Some live batches overlapped: each used four workers, with combined concurrency
occasionally eight. Provider caches and load were uncontrolled. Timing comparisons
are descriptive, not isolated causal benchmarks. Billed dollars are unavailable;
actual provider usage is retained, including development failures.

## Offline and documentation checks

Each invocation has its own log and JSON metric inventory. The final backend run
is [backend-6.log](backend-6.log): 515 passed, 1 skipped, with
one existing dependency deprecation warning. Earlier passing runs remain recorded.
`targeted-1.json` initially serialized its count mapping backwards; its raw log
correctly records 33 passed. Later count records use named numeric fields.
Mocked checks measure test duration only; live quality, provider cost and production
performance are marked not applicable.

No frontend behavior changed. No new live RAG benchmark or browser workload was
run to fill irrelevant metrics. See the final review for live results and remaining
limitations. Passing these checks does not authorize merging.
