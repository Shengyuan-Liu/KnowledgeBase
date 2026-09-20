# Recorded RAG evaluations

Evaluate the actual `answer_question` service on the [25 frozen NYU cases](nyu-test-cases.md).
Each run indexes only the 16 TXT documents listed in the [corpus manifest](materials/nyu/manifest.json)
into a fresh, isolated index. References and expected answers never enter the answering prompt.
Generation and grading are separate: use human ratings, an LLM judge, or both as successive reviews.

Recorded inspections:

- [Nine-case baseline failure audit](analyses/2026-09-20-baseline-failures.md):
  retrieved evidence, answer failures, judge attribution issues, and the next paired
  chunk-size experiment. This qualitative audit does not replace recorded scores.
- [Real-provider browser acceptance](browser-runs/20260920T225644765Z-96618e0c/README.md):
  an isolated synthetic functional workflow, separate from the 25-case RAG baseline.

## Run a baseline

Run these commands from the repository root. The existing `.env` supplies `OPENAI_API_KEY`.
`run` sends the corpus to the embedding provider and questions/retrieved text to the answer model.
`grade --judge-model` sends questions, references, answers, and retrieved text to the judge.
Both commands make paid API calls. Human grading, reporting, and comparison are offline.

```bash
uv run --locked python -m evals.evaluate run --label "Baseline: default chunking and top-k"
```

The command prints a unique directory such as `evals/runs/<run-id>/`. Replace `<run-id>` below
with that directory's name. Defaults match the current application: `gpt-4.1-nano`,
`text-embedding-3-small`, 256-character chunks, 64-character overlap, cosine distance, and top-k 5.
Override them with `--model`, `--embedding-model`, `--chunk-size`, `--overlap`, and `--top-k`.
`--cases` accepts an alternative JSONL in the same format, grounded in the same NYU manifest.

## Grade answers

For human grading, read the generated Markdown report, copy `review-template.json` to
`human-scores.json`, and replace its null/empty fields with your ratings. Include only cases you
have actually assessed and whose answer status is `ok`. Import a partial file to save progress:

```bash
uv run --locked python -m evals.evaluate grade evals/runs/<run-id> --reviewer Lucas --scores evals/runs/<run-id>/human-scores.json
```

Alternatively, use an LLM judge:

```bash
uv run --locked python -m evals.evaluate grade evals/runs/<run-id> --reviewer gpt-4.1-mini-v1 --judge-model gpt-4.1-mini
```

The evaluator uses the existing project's LLM client. Judge output is validated once, with no
automatic repair; failed calls and invalid outputs are recorded as review errors, never passing
scores. Repeating a grade command appends a new review for each submitted case. Earlier reviews
and report snapshots remain available. The latest attempt per case determines the current report;
a failed new review makes that case pending until it is reviewed successfully. Run one grading
process per run at a time. Human imports are validated in full before any reviews are appended.

The rubric is versioned in [evaluate.py](evaluate.py) and copied into every run:

| Field | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Each expected answer point | Missing or wrong | Partially correct | Complete and correct |
| Groundedness | Major unsupported claims | Minor unsupported claims | Supported by retrieved evidence |
| Citation support | Missing, invalid, or unsupported | Incomplete support | All substantive claims have supporting citations |
| Abstention, unanswerable only | Invents requested details | Vague acknowledgment | Explicitly acknowledges missing information without invention |

`abstention` must be null for answerable cases. `citation_support` may be null for an
unanswerable case with no factual claims requiring citations. Every rating needs explanatory
`notes` and an `issues` list (empty when no failures were found). Accept equivalent wording and
verified alternative source passages. Expected references assess correctness; actual retrieved
sources assess grounding. A correct fact unsupported by retrieved text loses grounding credit.

An answer passes only when every expected point and every applicable dimension receives 2.
The answer-point percentage averages points within each question, then averages scored questions
equally. It is a completeness/correctness metric, not an overall quality score. Reports separately
show grounding, citations, and abstention, with their denominators. Missing grades are null.
The overall pass rate is withheld until the run has finished and every successful answer has a
valid latest rating. Generation errors then count as failures in the full dataset denominator.

## Inspect history and compare experiments

```bash
uv run --locked python -m evals.evaluate history
uv run --locked python -m evals.evaluate report evals/runs/<run-id>
uv run --locked python -m evals.evaluate compare evals/runs/<baseline-id> evals/runs/<candidate-id>
```

Comparisons save a new JSON artifact under `evals/comparisons/`, including configuration changes,
aggregate deltas, and each question's before/after score and pass status. Positive answer-score
deltas indicate improvement; positive latency deltas indicate slower responses. Rate deltas are
fractions (0.10 means 10 percentage points). Comparisons suppress deltas when the dataset, corpus,
rubric, evaluator identity, judge protocol, or reviewed-case coverage differs, or either evaluation is incomplete.
Use the same reviewer ID and judge model consistently; do not reuse a reviewer ID for another person.
For revised rubrics, start a new evaluation series using the matching evaluator code version.

Change one factor at a time and state the hypothesis in `--label`, for example:

```bash
uv run --locked python -m evals.evaluate run --label "Larger chunks: does more context improve completeness?" --chunk-size 512 --overlap 64
```

### Automatic diagnostics

- **Citation number checks:** new answers retain `citation_check` with valid/invalid
  source IDs and a no-citations flag. Reports count checked answers, those with invalid
  IDs, and those without numbered citations. Legacy answers lacking this field are
  shown as not recorded. These counts do not judge factual support or automatically
  fail an answer without citations; the [citation guide](../docs/citations.md) defines
  the supported syntax and limitations.
- **Annotated character recall:** for each reference span, compute the fraction covered by the
  union of retrieved chunk offsets from the correct document; average spans within each question,
  then average successful answerable questions. Overlapping chunks do not count twice.
- **Full evidence recall:** fraction of annotated spans fully covered by that union, with the same
  averaging. A filename match alone gets no credit. Valid alternative passages in duplicate
  documents may earn low annotated recall; inspect those cases semantically before diagnosing a miss.
- Both retrieval metrics are null for unanswerable cases; their context evidence is not a positive
  retrieval target. Generation failures are excluded from retrieval means and counted separately.
- **Latency:** wall time for a successful question's retrieval, generation, and evaluation source
  offset lookup. Excludes ingestion and judging. P50 uses the median, P95 nearest rank. Error attempt
  latencies remain in raw records; these timings are not a controlled performance benchmark.

## What is retained

| Artifact in each run directory | Purpose |
| --- | --- |
| `run.json` | Run label, timestamps, status, settings, code commit/dirty state, implementation and lockfile hashes, dataset/corpus hashes, rubric |
| `cases.json`, `corpus.json` | Exact questions, reference answers, evidence, case notes, and source manifest |
| `answers.jsonl` | Per-question answers, complete retrieved text and offsets, automatic retrieval scores, latency, or error type |
| `review-template.json` | Blank human scoring form; no invented scores |
| `reviews.jsonl` | Append-only reviews, reviewer/method/model, evaluator code revision, judge protocol hash, exact messages and raw response, scores, reasons, issues, answer hash |
| `reports/` | New timestamped Markdown and JSON snapshots after each run, grading session, or explicit report |

Do not edit original answers or old reviews; append another review instead. Answer hashes prevent
reusing a rating after the recorded answer changes. These are ordinary Git-tracked artifacts, not
a tamper-proof database. Keep commits for meaningful runs and inspect the dirty flag. Local SQLite
and Chroma indexes live in ignored `data/evals/<run-id>/`; they are not evaluation evidence.
Completed questions survive a later interruption. A failed ingestion or interrupted run retains its
status and completed records; start a new run to retry. Exceptions retain their type, not potentially
secret provider messages. The harness records neither token usage nor monetary cost because the
current application clients return only text/vectors; do not infer either from latency.

## Using results in a resume

These 25 questions are a small **development/regression set**, not a held-out test set. A first run
is a baseline, not improvement. Keep bad runs and regressions. To claim improvement, cite two
comparable run IDs, the exact metric and denominator, the change tested, and your own engineering
contribution. Report LLM scores as LLM judgments, not objective accuracy or human ratings. Model
aliases can change, and the provider calls are stochastic; repeat promising comparisons and inspect
disagreements manually, especially refusals and citations. Add a separately frozen, unseen test set
before making broader quality claims. Never turn a test fixture or mock response into resume evidence.

## Verification

```bash
uv run --locked python -m pytest tests/test_evaluation.py
make test
```

Tests use offline fixtures and fake judge outputs. They verify scoring, denominators, reference
spans, comparison eligibility, persistence, and failures; their passing counts are not RAG scores.
