# Budgeted Source Identity for Generation

Status: implemented on `v1`, pending user acceptance and merge approval. Source
identity and context accounting are verified; remaining generation errors mean
this is not a claim of complete RAG answer quality.

## Delivered behavior

Every numbered context region now includes a `Source metadata` JSON label with
its actual `file_name` and `heading_path`, followed by `Excerpt:` and the unchanged
canonical text. Flat or unheaded text uses an empty heading list. No title or
heading is inferred. Parent and retained-child sources keep their existing IDs,
offsets, text, provenance and citation numbers in the response.

`build_context()` is shared by evidence packing and generation. The 4,096-token
budget includes file names, heading paths, labels, excerpt text and separators.
System instructions and the question remain outside this evidence budget.
New packing diagnostics record `context_format: "source-metadata-v1"`; old
snapshots without that field read as null. Old answers are not repacked.

Generation instructions explain that different files identify distinct sources
and metadata is not additional factual evidence. The
[initial experiment](../20260924T145921Z-source-metadata/README.md) exposed
nonstandard citations and raw metadata output. The final prompt explicitly
requires numeric `[n]` citations and prohibits emitting metadata objects. There
is no post-generation answer repair, additional model call, new configuration
switch, or change to retrieval/reranking.

## Comparison design

- Same 18 frozen questions and annotations, 16 answerable and two unanswerable.
  Same library snapshot: 17 Ready files, 38 parents and 92 children.
- Same selected top-5 children and BGE rankings from the previous active-library
  run. Each arm freshly executes production packing and generation. Query
  embedding, search and reranking are not rerun. Their old traces remain in
  `frozen-evidence.jsonl`, not counted as fresh timings.
- 36 fresh GPT-4.1 streamed generation calls, alternating arm order, concurrency 1,
  timeout 60 seconds, zero retries and no warmup. Returned model names and usage
  are saved. Network/provider cache and host load were uncontrolled, and backend
  checks overlapped part of the run. No model loading is included in replay time.
- Baseline uses pre-metadata formatting/instructions. Candidate uses metadata,
  budget-aware repacking and corresponding identity/output rules. This measures
  the complete change, not the isolated causal effect of one prompt sentence.
- One sample per case/arm, using development questions rather than held-out data.
  Baseline and candidate messages, outputs, traces and usage are retained in
  `answers.jsonl`; input/code hashes and settings are in `run.json`.

## Evidence and ranking

| Metric | Baseline | Candidate |
| --- | ---: | ---: |
| Annotated-character recall, mean over 16 cases | 99.96% | 99.96% |
| Full annotated-span recall, mean over 16 cases | 68.75% | 68.75% |
| CPT annotated-character/full-span recall | 100% / 100% | 100% / 100% |
| GPA annotated-character/full-span recall | 100% / 100% | 100% / 100% |

No per-question annotated coverage decreased. Five source lists changed under the
same budget: GPA, personal schedule, admissions prerequisites, CPT and exact
tuition. For CPT, the unrelated admissions-requirements child no longer fits;
the required FAQ child remains. Different source counts do not imply lost facts.
`input-audit.json` records all source-list and coverage changes. `source-audit.json`
checks all 36 contexts against their actual model input, canonical text/offsets,
metadata and token budget, and measures identity overhead on the same source set.

The unchanged frozen top-5 child diagnostics are Recall@5 0.7795, Precision@5
0.3500, Hit Rate@5 0.9375, MRR@5 0.9375 and NDCG@5 0.8336. These are **binary
gold-span-overlap proxies**, not exhaustive semantic relevance judgments: a child
is positive if its interval overlaps a marked span, all other children count as
zero, and broad annotations may include irrelevant text. MRR is truncated at 5;
NDCG uses binary gains/log2 discount, precision denominator is 5, and the two
unanswerable questions are excluded. `ranking-diagnostics.json` retains labels
and per-case scores. No retrieval gain is claimed.

## Answer inspection and known failures

Codex reviewed all 36 answers against frozen expected points and topical relevance.
This is development review, not independent human grading or exhaustive claim
adjudication. `development-reviews.jsonl` records exact answers, scores and issues.

- **Source identity:** the final candidate CPT answer uses source [1] for Industry
  Concentration and [4] for the admissions FAQ without grouping the general FAQ
  [3] under the admissions heading. The fresh baseline still groups `[3], [4]`
  under that heading. Both arms state the three required facts. The candidate
  still adds interpretation about arranging authorization earlier than standard;
  source labeling does not guarantee restraint in interpretation.
- **New extra factual error:** the candidate credit-plan answer says first fall
  has “3 required/core courses.” The supplied plan lists two required courses
  plus a general elective/track course. The baseline lists the correct mixture.
  The narrow expected points (36 credits, 9 per semester, availability caveat)
  still pass, showing why point coverage is not full factual accuracy.
- **Unchanged rubric issue:** both API-setup answers omit `anthropic.Anthropic()`
  from the composite expected-point annotation. The question only explicitly
  asks for the invoking method; the broader frozen annotation was not changed.
- **Citation syntax:** all 18 final candidate outputs have recognized numeric
  citations, no out-of-range IDs, no observed `[cite: n]`/`[source n]` forms and no
  raw metadata objects. Baseline also passes these syntax checks. This does not
  establish semantic citation support or full claim coverage.
- Both unanswerable questions appropriately acknowledge missing information in
  both arms. No answerable question falsely refuses a requested part in the
  focused absence review.

Expected-point normalized scores are 99.07% in both arms, and fully correct/complete
point fractions average 98.15% in both arms over 18 questions. Topical relevance
averages 2/2 in both arms under the recorded narrow rubric. These scores exclude
unmodeled extra claims and **must not be described as overall answer accuracy**.
Full faithfulness, citation support and citation coverage are marked unavailable:
the previously observed judge claim omissions were not repaired or rerun in this
task, and exhaustive claim review is missing. Concrete failures remain visible.

## Timing, tokens and reliability

| Timing, seconds | Baseline mean / P50 / P95 | Candidate mean / P50 / P95 |
| --- | ---: | ---: |
| Generation first nonempty delta | 0.746 / 0.705 / 1.233 | 0.876 / 0.742 / 3.643 |
| Complete generation stream | 2.819 / 2.216 / 5.394 | 2.496 / 2.208 / 5.130 |
| Packing | 0.00516 / 0.00479 / 0.01243 | 0.00551 / 0.00511 / 0.01131 |

Each distribution has 18 samples; nearest-rank P95 is the maximum. First-delta
and stream-completion times cover the generation SDK call only, excluding app
HTTP and upstream retrieval. Mean completion decreased in this sample but first
delta increased; do not claim a general speedup from a single pass.

| Provider tokens, totals over 18 calls | Baseline | Candidate |
| --- | ---: | ---: |
| Input | 60,875 | 61,449 |
| Output | 4,316 | 3,095 |

All 36 generation requests completed with zero errors, timeouts or retries. No
embedding or rerank provider requests were made in replay. Billed cost is
unavailable, not zero; no estimated dollars substitute for billing. Active-time
sequential throughput is recorded but does not measure load capacity.
`metrics-reviewed.json` is the full metric inventory with review provenance and
missing/not-applicable reasons; `metrics.json` retains pre-review diagnostics.
Ingestion/update/delete metrics are not applicable to this generation experiment.

## Verification and restored application

- Final backend suite: **479 passed, 1 skipped**, 13.76 seconds. Raw output and
  complete offline metric statuses are in `backend-tests.log` and `offline-checks.json`.
- Browser lifecycle/evidence checks: **9 passed** in the initial metadata run;
  formatter and UI were unchanged by the final prompt wording. No frontend code
  changed. JSON/SSE tests verify shared metadata-bearing context, and history
  tests preserve exact child/parent evidence after source deletion and restart.
- Regression coverage includes nested headings, Unicode/CRLF fenced-code text,
  empty heading paths, metadata consuming the budget, exact boundaries and
  historical format values staying null. The initial eight fixture-budget
  failures and their corrected results are retained in the initial run.
- The final live app smoke had one startup-readiness connection failure before
  any RAG request was sent. Its traceback and metrics are preserved. After the
  app became ready, the request completed with **4.296 seconds to first delta**
  and **6.884 seconds total**. This single actual HTTP request is recorded
  separately in `app-smoke.json` and `app-smoke-metrics.json`.
- The smoke identifies the correct FAQ and concentration sources, but still
  characterizes the FAQ as general CPT guidance. It does not prove full policy
  interpretation correctness. All 17 files and ten existing conversations were
  preserved; one final smoke conversation was added. Across both attempts there
  are two new smoke conversations. No source files were uploaded/deleted/reindexed.

The API is restored with the final prompt and context format. Historical evidence
remains readable. The source-identity feature is ready for user review; fixing
claim-level evaluation and broader generation errors remains separate work.

Run harnesses from the repository root with `PYTHONPATH=.` in a new run directory;
outputs refuse overwrite. Frozen-candidate replay does not require stopping the
API. Provider event instrumentation is reused from the committed preceding
source-attribution run; no hidden evaluation route or production control was added.
