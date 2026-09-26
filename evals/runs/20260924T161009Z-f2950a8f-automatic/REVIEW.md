# One-command evaluation delivery review

`make eval` now ingests the frozen 17-document corpus into an isolated index, runs
all 18 questions through production retrieval/reranking/packing/streaming, performs
a two-pass LLM claim review, prints metrics and compares a prior compatible run.
The existing application library and conversations were not modified.

## Execution and evidence

The full RAG batch was executed in
[`20260924T154305Z-4ef1ccf3-automatic`](../20260924T154305Z-4ef1ccf3-automatic/README-recovered.md).
Subsequent runs reused those exact answers while fixing the judge/reporting code;
this final run performs fresh protocol-4 judgments, not fresh RAG generation.

- RAG: **18/18 succeeded**; 62 supplied excerpts match canonical document offsets,
  all evidence budgets passed. Seventeen of eighteen source lists exactly match the
  previous experiment; evidence coverage is unchanged on every question.
- Current judge: **15/18 valid**, 3 pending (waiver, personal schedule, API setup).
- Previous-answer regrade: **17/18 valid**. Comparison uses **15 matched valid pairs**.
- The command intentionally exits nonzero when current judgments remain invalid.
  Reports, valid scores and failure reasons are still saved; missing scores are not zeros.
- Backend verification: **508 passed, 1 skipped**. These are offline tests, not quality scores.

## Retrieval and timing

| Metric | Previous | Current | Qualification |
| --- | --- | --- | --- |
| Annotated character coverage | 99.96% | 99.96% | 16 answerable cases; exact source-span union |
| Fully covered gold spans | 68.75% | 68.75% | Same annotations, macro-average |
| Mean generation duration | 2.50 s | 2.16 s | Generation-only, 18 observations per side; no causal speed claim |
| Mean first answer delta | Not measured end-to-end | 4.06 s | In-process service, including retrieval, excluding HTTP/judge |
| Mean complete response | Not measured end-to-end | 5.35 s | Includes retrieval, generation and persistence; excludes HTTP/judge |

Current complete-response P50/P95: **5.27/7.97 seconds**; first-delta P50/P95:
**4.04/5.50 seconds**. P50 is the median and P95 nearest rank. Ingestion and local
model loading are separate. The original interrupted run did not persist its batch
wall interval, so throughput is explicitly unavailable for these reused observations;
the runner now persists that interval immediately after RAG completes.

## Paired automatic judgments

These values are **LLM assessments on 15 common valid cases**, not objective
accuracy or full-set improvement. The judge is `gpt-5.4-mini`, medium reasoning,
4 concurrent reviews; the RAG batch is sequential.

| Metric | Previous | Current |
| --- | --- | --- |
| answer_correctness | 100.00% | 100.00% |
| answer_completeness | 100.00% | 100.00% |
| faithfulness | 98.09% | 97.78% |
| citation_support | 98.11% | 99.17% |
| citation_coverage | 66.23% | 64.56% |

Expected-point correctness is not overall correctness: the new judge detects the
previous MSDS answer's extra assertion that three first-fall courses are required,
although the sample plan contains two required courses and one elective.

**Known judge limitations remain.** The current prerequisites review has a false
positive caused by an extracted claim dropping a qualifier present in the answer.
The GPA and source-provenance judgments also warrant inspection. Citation coverage
uses a conservative same-line boundary and may undercount references after lists.
Full-set pass rates are withheld because reviews are pending. See the
[focused development inspection](development-review.md); raw scores were not
manually corrected to manufacture a clean pass.

## Records and configuration

- [Complete console-equivalent report](README.md), [metrics JSON](summary.json),
  [paired case comparison](comparison.json), [judge records](reviews.jsonl).
- [Metric definitions and commands](../../metrics.md), including optional
  `make eval EVAL_ARGS="--answers-from evals/runs/<run-id>"` for paid regrading only.
- [Verification and calibration history](../../check-runs/20260924-automatic-eval/README.md).
- `.env` retains the existing key. Judge configuration is `JUDGE_MODEL=gpt-5.4-mini`,
  `JUDGE_REASONING_EFFORT=medium`, `JUDGE_TIMEOUT_SECONDS=180`, `JUDGE_CONCURRENCY=4`.
  The RAG answer model remains `gpt-4.1`.
- Billing dollars, separately timed search/fusion, and missing failed-call usage
  remain unavailable. Update/delete is not exercised. See the full metric inventory.

This change is on `v1`. Tests and scores do not authorize a merge into `main`.
