# DeepSeek RAG evaluation package

Evaluate KnowledgeBase on a frozen, technical documentation corpus with
**320 single-turn questions**, **12 conversations / 36 turns**, and a
**42-question latency subset**. All questions and project-facing text are English.

The deliverable is prepared evaluation data and offline-verified tooling.
**No live accuracy, latency, token-usage or cost results have been measured for
this package.** [validation.json](validation.json) describes artifact integrity,
not RAG quality.

## Files

| File | Use |
| --- | --- |
| [Corpus and catalog](../materials/deepseek/README.md) | 89 source MD files and 89 identical TXT import copies |
| [cases.jsonl](cases.jsonl) | All 320 single-turn cases, answers and exact evidence |
| [cases.md](cases.md) | Human-readable question and answer-point catalog |
| [dev.jsonl](dev.jsonl) | 271 development questions |
| [test.jsonl](test.jsonl) | 49 reserved family-split questions |
| [conversations.jsonl](conversations.jsonl) | 12 independent conversations, 3 turns each |
| [latency-cases.jsonl](latency-cases.jsonl) | 42 development cases across all seven categories |
| [workloads.json](workloads.json) | Quality, repeated timing, concurrent load and conversation protocols |
| [metrics.md](metrics.md) | Metric definitions, denominators, interpretation and comparison protocol |
| [coverage.json](coverage.json) | Category counts and document-to-question mapping |
| [validation.json](validation.json) | Offline integrity results |
| [tools/](tools/) | Capture, build, validate, HTTP benchmark and offline human-grading tools |

## Question composition

| Category | Count | What it probes |
| --- | ---: | --- |
| Semantic | 109 | Paraphrases, workflow explanations, implications and troubleshooting |
| Keyword | 147 | Exact field names, paths, error codes, versions, environment variables and opaque call IDs |
| Multi-document | 12 | Answers requiring information from more than one page |
| Numeric | 7 | Specific price-table cells, units and a derived cost calculation |
| Historical | 19 | Correctly scoped release facts and change-log footnotes |
| Source conflict | 6 | Stale announcements, API-family differences and source anomalies |
| Unanswerable | 20 | Missing personal state, future facts, nonexistent documented endpoints and absent measurements |

Opaque strings such as `call_00_H2SCW6136vWJGq9SQlBuhVt4` and the distinction
between `requiresAssistantContentForToolCalls` and other compatibility keys make
lexical matching important. These are **keyword-sensitive** questions; the label
does not prove that a dense retriever can never answer them. Compare lexical,
dense and hybrid retrieval empirically if those implementations become available.
The current project uses dense retrieval; this package does not change it.

Every captured document has at least one positive-evidence or related-background
reference in the cases. This is document coverage, not exhaustive coverage of
every individual statement. Semantic/keyword variants of the same authored fact
family share a split. The split is deterministic and frozen in Git. Fact families
reused by the development conversations are kept in development. Different
families and multi-document questions can still overlap in source facts, and the
public documentation may occur in model training data. Therefore this is a
reserved development benchmark split, **not proof of leakage-free generalization**.
Do not tune on the reserved test answers; create an independently authored unseen
set before making broader generalization claims.

## Case format and scoring

Each JSONL row includes `id`, `corpus_id`, `family_id`, `split`, `category`,
`difficulty`, `question`, `answerable`, `expected_answer_points`, `evidence`,
`exact_answer_tokens`, `tags` and `scoring_notes`.

Evidence includes the source URL, Markdown/TXT paths, exact quote, line range,
character offsets and 1-based answer-point numbers it supports. Offsets are
**zero-based, half-open Unicode code-point offsets**, matching Python `str`
slicing, not UTF-8 byte offsets or JavaScript UTF-16 indices. Line numbers are
1-based. An evidence list gives annotated supporting passages, not every possible
valid passage in duplicate or overlapping documentation.

For unanswerable cases, `evidence` is empty. `context_evidence` is only related
background and is not a positive retrieval target or proof of corpus-wide absence.
Grade an explicit, evidence-bound refusal as success; do not demand citations for
pure acknowledgments of missing information. The absence labels were authored
against this snapshot and must be reconsidered if the corpus changes.

For multi-turn cases, send only `question` for each turn and reuse the returned
conversation ID. `standalone_reference_question`, expected answers and evidence
are evaluation metadata, never inputs to the answering system. A failure blocks
later turns in that scenario and remains visible in the denominator.

## Install and validate offline

Run from the repository root. Node.js 22 or later is required.

```bash
npm ci --prefix evals/deepseek/tools --no-audit --no-fund
npm test --prefix evals/deepseek/tools
node evals/deepseek/tools/validate.mjs
```

Validation makes no model calls. Tests cover corpus hashes, English text, identical
TXT copies, tables, hidden code tabs, exact evidence spans, split consistency,
Unicode offsets, overlapping retrieval spans, incomplete streams, HTTP recording,
grading rules and failure denominators.

## Run against KnowledgeBase

The existing Python evaluator hardcodes the NYU manifest. Passing these cases to
`python -m evals.evaluate run --cases ...` alone will **not** work. This package
provides an independent JavaScript client for the existing file and streaming-chat
HTTP endpoints; no Python implementation or application behavior was modified.

The server continues to obtain local credentials from the project's ignored `.env`.
Corpus upload calls the configured embedding provider, and questions call the
configured answer/resolver providers. Those are paid/provider operations when
using real credentials; the commands below are instructions, not recorded runs.
DeepSeek is the **subject of the documents**, not a requirement to switch the
project's model provider to DeepSeek.

Start a separate instance with a new data directory and port. Do not reuse a data
directory owned by another running process:

```bash
DATA_DIR=data/deepseek-eval uv run --locked uvicorn knowledgebase.api.app:create_app --factory --host 127.0.0.1 --port 8011
```

In another terminal, index the TXT corpus. The client requires an empty instance,
records the exact uploaded IDs, and never deletes existing documents:

```bash
mkdir -p evals/deepseek/runs
node evals/deepseek/tools/run.mjs ingest --base-url http://127.0.0.1:8011 --out evals/deepseek/runs/ingestion-01
```

Run development quality questions:

```bash
node evals/deepseek/tools/run.mjs run --base-url http://127.0.0.1:8011 --ingestion evals/deepseek/runs/ingestion-01/ingestion.json --cases evals/deepseek/dev.jsonl --out evals/deepseek/runs/dev-01
```

Use a **new output directory for every command**. The recorded file inventory
must still match. Do not switch data directories, change uploaded files or mix
other corpora during a run. A failed ingestion leaves its record and any uploaded
files for inspection; start a new isolated instance/directory for a clean retry.

Repeated timing and conversations:

```bash
node evals/deepseek/tools/run.mjs run --base-url http://127.0.0.1:8011 --ingestion evals/deepseek/runs/ingestion-01/ingestion.json --cases evals/deepseek/latency-cases.jsonl --repeat 5 --concurrency 1 --out evals/deepseek/runs/latency-01
node evals/deepseek/tools/run.mjs conversation --base-url http://127.0.0.1:8011 --ingestion evals/deepseek/runs/ingestion-01/ingestion.json --out evals/deepseek/runs/conversation-01
```

For load diagnostics, repeat the same latency workload with `--concurrency 2` and
then `4` in distinct output directories. Each single-turn request starts a new
conversation; each multi-turn scenario keeps its own conversation, with sequential
turns. The default answer timeout is 180000 ms; use `--timeout-ms` to change it.

The client saves `run.json`, frozen `cases.jsonl` and `manifest.json`, per-attempt
`answers.jsonl`, `metrics.json` and a blank `review-template.json`. It records full
answers and retrieved text, source timing, first answer-text timing, final
completion timing, errors and retrieval diagnostics. Failed requests are not
automatically retried. EOF without the application `complete` event is an error,
even if partial answer text was received.

The client records its Git revision but cannot introspect the server's actual
model settings. Add `--config PATH_TO_JSON` with nonsecret experiment metadata:
server Git revision, model identifiers, chunk size/overlap, top-k, history limit,
machine/network and cache-state notes. Never include credentials. Without this,
the run's `server_configuration` is null and a model/configuration comparison is
not adequately controlled.

## Grade factual quality offline

Copy a run's review template to a new human-review JSON file. For every assessed
successful answer, fill:

- `point_scores`: one 0/1/2 score per expected point (wrong/missing, partial, complete).
- `groundedness`: 0/1/2 for major unsupported claims, minor unsupported claims, fully supported.
- `citation_support`: 0/1/2 for absent/invalid, partial, complete support. Null is
  allowed only for an unanswerable case with no factual claims requiring citations.
- `abstention`: null for answerable cases; 0/1/2 for invented specifics, incomplete
  acknowledgment, explicit missing-information acknowledgment without invention.
- `reviewer`, evidence-backed `notes`, and `issues` (empty if none).

Preserve identity and `answer_sha256`. For partial grading, include only completed
reviews; blank templates are intentionally rejected. Compare reference answers
for correctness, but use **actual retrieved text** to judge grounding and citation
support. Quote relevant answer and source text in your notes. Accept correct
alternative passages. A source citation number alone does not prove support.

```bash
node evals/deepseek/tools/grade.mjs evals/deepseek/runs/dev-01 evals/deepseek/runs/dev-01/human-reviews.json
```

The result is a new timestamped quality JSON report. It gives answer-point
accuracy, strict full-pass rate, grounding, citations, abstention and category
breakdowns. Missing reviews remain pending and suppress the overall pass rate;
errors count as failures once grading is complete. No LLM judge is invoked by
these tools. If an LLM judge is added later, label its results separately and
calibrate disagreements with human review.

## Rebuild or refresh

Hand-authored fact definitions live in `tools/build-cases.mjs`,
`tools/case-extensions.mjs` and `tools/case-suites.mjs`. Rebuild offsets, indexes and
workloads after an intentional corpus change:

```bash
node evals/deepseek/tools/build-cases.mjs
node evals/deepseek/tools/build-workloads.mjs
node evals/deepseek/tools/validate.mjs
```

`capture.mjs` and `capture-faq.mjs` reproduce the extraction procedure from the
live websites. **They overwrite the snapshot.** Refresh on a new branch, assign a
new corpus ID/date, inspect changed source claims, revise gold answers, regenerate
the catalog and revalidate. Do not silently refresh sources between paired runs.
The optional `capture.mjs --cached` uses the capture HTML cache under `/tmp` from
the same local session; that cache is not a committed artifact.
