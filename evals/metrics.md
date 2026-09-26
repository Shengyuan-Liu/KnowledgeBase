# Automated RAG evaluation and metric definitions

Run `make eval` from the repository root. It uses the existing `.env` credentials
and `Settings`: `ANSWER_MODEL`, `EMBEDDING_MODEL`, `JUDGE_MODEL`, chunking, hybrid
retrieval, reranker and context budgets. It makes paid embedding, answer and judge
API calls. SDK retries are deliberately disabled for observable attempt accounting;
`EVAL_TIMEOUT_SECONDS` applies to individual RAG provider requests;
`JUDGE_TIMEOUT_SECONDS` (default 180 seconds) separately bounds each judge call. No question-level
hard deadline is imposed on local retrieval/model loading.

The command automatically creates an isolated index, ingests the frozen **17-document,
18-question** development benchmark, runs the production conversational streaming
service with a fresh conversation per question, grades successful answers, finds a
previous comparable evaluation, prints metrics/deltas, and writes an immutable new
run directory under `evals/runs/<timestamp>-<id>-automatic/`. The API server need not
be running. Existing application documents and conversations are untouched.
The isolated index/history live under `<DATA_DIR>/evals/<run-id>/`.

The benchmark contains the same 16 NYU TXT documents and one DeepSeek Markdown
file used by the preceding library experiments. [Cases](benchmark/cases.json) and
[corpus hashes](benchmark/corpus.json) freeze questions, annotations and document
bytes. References never enter the answering prompt. This is a small regression set,
not a held-out test or general RAG accuracy measurement. The older
`python -m evals.evaluate` commands remain available for the historical 25-case NYU
suite and protocol 3; their scores must not be pooled with this benchmark.

## LLM-as-a-judge protocol

`claim-inventory-v11` has three calls per successful judgment:

1. Split the original answer deterministically into every nonempty line. The judge
   classifies assertions within every line (including mixed factual/refusal lines)
   and lists atomic factual claims bound to the full original answer unit,
   including extra details, code, tables and source attribution. Every nonempty line must contain classified items; omitted/duplicate lines are rejected.
2. A source-blind call audits the inventory against the original answer. It receives
   only answer units and the inventory, never sources, reference points or calibration
   labels. Reported extraction issues stop the review before evidence grading.
3. A final call assesses each claim against the **actual supplied sources**.
   It separately scores expected points, relevance, citations and
   refusal behavior. Supported and contradicted claims select numbered source lines; the evaluator
   records their exact text directly, avoiding model-generated quote paraphrases.
   All inventoried claims must be assessed in order. Reported omissions, fabricated
   answer quotes, absent source/line IDs or untraceable citation assignments invalidate the review.

Extraction preserves alternatives, conditions, negation, categories and restrictive
qualifiers. Atomic claims must retain their original logical scope. Documented
installation/configuration instructions count as factual claims. The second pass
audits extraction against the original answer only; a faithfully extracted but
unsupported answer claim receives a support verdict, not an inventory error.
`inventory_audit` retains extraction issues and `assessment_attempt` retains an
attempted evidence assessment before validation. Invalid extraction never becomes
an answer score. The additional source-blind audit is measured separately.
Faithful nonexhaustive list paraphrases are allowed. Editorial phrases such as
"main requirements" are not interpreted as official priority or exclusivity unless
the answer explicitly asserts that meaning; substantive requirements remain factual.
Source lead-ins do not create claims about the answer's own production history.
Specific source-attributed facts are still assessed. Nested-field summaries are
resolved in answer context: an ignored child parameter does not mean its parent
object is unsupported. Absence of evidence is insufficient, not contradiction.

The assessment request now nests refusal fields under `abstention`. Its strict
schema permits only the combinations below. Explicit refusals require at least
one existing answer unit; a non-refusal requires an empty unit list.

| Actual refusal | Justified refusal | Appropriate unanswerable refusal | Availability |
| --- | --- | --- | --- |
| false | false | false | All cases |
| true | false | false | All cases |
| true | true | false | All cases, including a partial refusal with invented details |
| true | true | true | Unanswerable cases only |

These flags describe observed answer behavior, not what the answer should have
done. The stored assessment retains its existing flat fields through a lossless
shape conversion; values are never repaired or inferred. Raw API output retains
the nested shape. Semantic mistakes can still occur within a legal state.
The nested `anyOf` design follows the supported
[Structured Outputs schema subset](https://developers.openai.com/api/docs/guides/structured-outputs).

Run `make eval-calibrate` to check the judge against the
[fixed calibration set](calibration/cases.json). It calls only the judge, uses the
same `.env` judge settings, prints the full applicable metric inventory and saves
new records in `evals/calibration-runs/`. Correct answers, altered facts and refusal
cases have frozen expectations that are not sent to the judge. Missing factual
claims cannot silently pass. Pending reviews count against overall agreement but
are reported separately from wrong decisions. This command exits nonzero for any
label mismatch or pending review. Labels are Codex-authored development regressions,
not independent human annotations or held-out accuracy. See the
[calibration guide](calibration/README.md) for scope and comparison results.
The [latest calibration review](check-runs/20260924-judge-abstention/REVIEW.md)
compares v11 with v10 on unchanged inputs. Historical contradictions remain in
their original artifacts; traceable output is not a guarantee of semantic correctness.

The three calls use `JUDGE_MODEL` (default `gpt-5.4-mini`) and
`JUDGE_REASONING_EFFORT` (default `high`; `off` omits the parameter for models that
do not support reasoning). [Official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
confirms structured outputs and the available reasoning levels. All stages use the same configured
model, not an independent human. Reviews run with `JUDGE_CONCURRENCY` workers (default 4), separately from the
sequential RAG batch. `judge-batch.json` records concurrency and wall time; per-review
judge latency excludes waiting for a worker. Expected-point and refusal evidence select answer unit IDs; exact answer text is
recovered by the evaluator. All prompts, schemas, raw responses, token usage,
resolved model IDs and protocol hash are retained. No repair, automatic retry or
silent passing score is applied. Invalid reviews remain pending; full-set pass rate
is withheld. The command returns nonzero for current RAG/judge operational failures, while
low quality scores are reported without pretending they are execution failures.
Historical regrade errors limit the comparison and remain visible in its records;
they do not invalidate otherwise complete current-run measurements.

Citation association is limited to the same nonempty answer line in this protocol;
citations placed only in a later summary are not inherited by earlier bullet lines.
This conservative boundary can undercount cross-line citation conventions.

These checks enforce traceability and explicit line coverage, **not semantic truth
or complete atomic-claim extraction**. A model can misclassify a line or accept an
irrelevant quote. Review representative failures. Expected-point correctness alone
cannot detect every additional error: consult contradicted/unsupported claims,
faithfulness and strict pass rate. In particular, the frozen prior MSDS answer says
three first-fall courses are required, while the source lists two required courses
and one elective. That is a judge calibration regression.

## Quality and retrieval metrics

Fractions use 0–1; multiply by 100 for percent. A delta of 0.01 is one percentage
point. Unless stated otherwise, scores average equally over applicable questions.
Every metric has a status, sample count, method, unit and raw artifact reference.
Unavailable or inapplicable values are never substituted with zero.

| Console / JSON name | Meaning and denominator |
| --- | --- |
| `recall_at_k` | Relevant retrieved children / all labeled relevant children. K is `RETRIEVAL_TOP_K`; stage is selected children before parent expansion. |
| `precision_at_k` | Relevant children in first K / K, including when fewer than K are returned. |
| `hit_rate_at_k` | Fraction of eligible questions with any relevant result in first K. |
| `mrr_at_k` | Reciprocal rank of first relevant result, zero for a miss, truncated at K. |
| `ndcg_at_k` | Binary-gain discounted relevance (`1/log2(rank+1)`) divided by ideal DCG at K. |
| `annotated_char_recall` | Fraction of gold source characters covered by the union of actual supplied excerpts; average gold spans per question, then questions. |
| `full_evidence_recall` | Fraction of gold spans completely covered by supplied excerpts, with the same averaging. |
| `answer_correctness` | Expected-point score: 0 wrong/missing, 1 partial, 2 fully correct; normalized and averaged. **Not overall answer accuracy.** |
| `answer_completeness` | Fraction of expected points actually attempted in the answer, independent of whether correct. |
| `fully_correct_points` | Fraction of expected points scored 2, combining full correctness and completeness. |
| `faithfulness` | Fraction of inventoried claims supported by supplied evidence. Claim-free answers are excluded. |
| `answer_relevance` | Judge score: 0 off-topic, 1 partly responsive/extraneous, 2 directly responsive, divided by 2. |
| `citation_support` | Supported claim–citation pairs / assessed claim–citation pairs per cited answer. Uncited answers are excluded here and penalized by coverage. |
| `citation_coverage` | Claims with at least one supporting inline citation / factual claims per answer. Claim-free answers excluded; invalid citations provide no coverage. |
| `appropriate_abstention` | Appropriate explicit refusal without invented specifics / validly judged unanswerable questions. |
| `incorrect_abstention` | Unjustified refusal despite available supplied evidence / validly judged answerable questions. |
| `answerable_refusal` | Any full/partial refusal / validly judged answerable questions, including retrieval-caused missing evidence. |
| `contradicted_claims` | Count of factual claims contradicted by supplied evidence, including extra claims beyond expected points. |
| `unsupported_claims` | Count of contradicted or insufficiently supported claims. |
| `claim_count` | Total factual claims in valid inventories. Different answer lengths change this denominator. |
| `strict_pass_rate` | All expected points correct, every factual claim supported and cited, relevance 2, and correct refusal behavior. Generation errors fail; missing judgments withhold the full-set rate. |

Ranking labels are **binary nonempty overlap with annotated gold spans**, not exhaustive
semantic relevance judgments. Unannotated children count as irrelevant; alternative
valid passages may be missed. Ranking scores are proxies, not calibrated retrieval
quality. Unanswerable questions have no gold ranking/coverage target and are excluded.
The child unit depends on chunk boundaries: compare stable source-span coverage
when chunking changes. All route rankings, selected children, reranker scores and
packing exclusions are retained separately in each answer's retrieval diagnostics.

## Performance, usage and reliability

| Name | Scope |
| --- | --- |
| `first_delta_seconds` | Production service invocation to first nonempty answer delta, including retrieval; excludes app HTTP transport. |
| `total_seconds` | Service invocation to completed iterator, including retrieval, generation and persistence; excludes judge, ingestion and model loading. |
| `generation_first_delta_seconds` | Generation SDK call to first nonempty provider text delta. |
| `generation_seconds` | Generation SDK call through stream close. |
| `retrieval_seconds` | Service invocation to sources event; includes thread scheduling, empty-history resolution and retrieval. |
| `embedding_seconds` | Query embedding provider call. |
| `rerank_seconds`, `packing_seconds` | Production diagnostics for those stages. |
| `search_fusion_seconds` | Unavailable until these stages have independent instrumentation; not inferred by subtracting noisy durations. |
| `judge_seconds` | Both inventory and assessment calls plus validation; separate from user-facing RAG response. |
| `token_usage` | Actual provider-reported tokens split by ingestion, query embedding, generation and judge. Failed requests may lack usage. |
| `cost` | Unavailable: billing dollars are not exposed by provider responses. Not inferred from token count or latency. |
| `evidence_tokens` | Exact formatted evidence-token counts, including filename/heading metadata. |
| `reliability` | Planned/attempted/success/error/not-attempted counts, success over planned cases, timeouts and retries. |
| `judge_reliability` | Valid/invalid/pending judgment counts. Quality metrics use valid applicable subsets and disclose N. |
| `concurrency_throughput` | Concurrency 1; successful RAG requests / measured batch wall time excluding ingestion and judging. Not a load capacity result. |
| `ingestion` | Per-document searchable ingestion duration, bytes, total duration, child count and physical index size before queries. |
| `model_loading` | Local reranker initialization, recorded separately from request latency. |
| `update_delete` | Not applicable: this workload creates fresh indexes and does not test lifecycle mutations. |

Timings include successful observations only and show sample count, mean, median
P50 and nearest-rank P95. Failure durations remain in raw records and failures stay
in reliability denominators. For 18 samples nearest-rank P95 is the maximum. No
warmup runs; provider caches, local caches, other app processes and network load are
uncontrolled. Stage durations may overlap and must not be added indiscriminately.

## Previous evaluation and comparison

The runner first finds the most recent completed automatic run with identical cases
and corpus hashes. Otherwise it searches historical library runs for matching cases,
all 18 candidate answers, matching document names and verified stored source slices.
A historical snapshot verifies stored slices, not previously unrecorded full-file
hashes; the first migration comparison explicitly retains this limitation.

Old answers are reused byte-for-byte. Existing judgments can be reused only with the
same protocol hash, judge model and answer hash and a valid status. Otherwise the
runner rejudges those saved answers and saves the new reviews in the **new** run
folder. This can add another two judge calls per previous answer. It never edits an
old run or reruns its generation. All future invocations normally need only the
current 18 answer calls and 36 judge calls, plus embeddings; inventory failures stop
that answer before its second judge call.

Full-set quality deltas are suppressed if either side lacks valid full-set judgments.
A separate paired-subset table compares only identical case IDs with valid applicable
judgments on both sides under the same judge protocol, with its own sample count.
This subset can be biased by failed reviews and is not a full-set quality result. Timing
deltas are suppressed where scopes differ (the preceding experiment only replayed
generation). New and old per-question evidence and reviews are retained even when
aggregate deltas are withheld. Different configurations are saved with comparisons;
changes in chunk boundaries invalidate direct child ranking comparisons. A single
stochastic before/after pass does not prove causality or a speed improvement.

## Saved artifacts

`run.json` records settings without credentials, code hashes, environment and timing
scope. `cases.json`/`corpus.json` freeze inputs; `chunks.json` captures index units;
`answers.jsonl` retains stream events, exact sources, diagnostics and per-case metrics;
`calls.jsonl` retains provider usage and actual generation/judge inputs;
`reviews.jsonl` retains both judge passes. `summary.json` and `README.md` contain the
complete metric inventory. `comparison.json` contains aggregates and paired cases.
`baseline-*` records retain imported previous answers and any fresh historical reviews.
The console prints the same metrics and available deltas with the output directory.

## Regrade saved answers without rerunning RAG

After a judge failure or a protocol change, preserve the failed run and use:

```bash
make eval EVAL_ARGS="--answers-from evals/runs/<run-id>"
```

This creates a **new** run, copies the complete successful RAG batch byte-for-byte,
records its original code/configuration and observation origin, and performs fresh
judgments. The reported RAG timings/ingestion are reused observations, not new
measurements. The source run stays unchanged. The default `make eval` always runs
a fresh index and RAG batch.

Latest development validation: [delivery review](runs/20260924T161009Z-f2950a8f-automatic/REVIEW.md), including pending judgments and observed judge mistakes.
