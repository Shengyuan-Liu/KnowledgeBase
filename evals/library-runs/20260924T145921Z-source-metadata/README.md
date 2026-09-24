# Source Identity Context: Initial Attempt

Status: retained initial experiment, superseded by the
[final output-format revision](../20260924T150609Z-source-metadata-v2/README.md).

Each source now carries file-name and heading-path metadata before its unchanged
excerpt. Packing counts the complete formatted context against the same 4,096-token
budget. This run compared 18 frozen questions under old/new formatting with fresh
production packing and generation. The selected child candidates and BGE ranks
were fixed; neither retrieval nor indexing ran. The exact candidate and baseline
prompts are preserved. This is a development workload, not held-out validation.

All 36 generation requests succeeded with zero retries. Coverage stayed at 99.96%
annotated-character recall and 68.75% full-span recall over 16 answerable questions.
The supplied source lists changed for five cases because metadata consumes budget,
but no annotated coverage decreased. CPT used the correct FAQ excerpt [4] and
concentration source [1] without grouping the general FAQ under admissions.
The fresh baseline also identified the correct sources in this sample; historical
source-name failures are not evidence of a measured accuracy delta here.

Two output-format issues prevented accepting this attempt unchanged:

- `api-setup` used `[cite: 1]`, so the app's numeric citation parser sees no citations.
- `msds-working-enrollment` used `[source 1, "..."]` in the body, although its
  summary also contained valid numeric citations.
- `msds-pathbreaker-fall2027` copied a raw metadata JSON object into the answer.

These are Codex development observations against actual outputs, not independent
human grading. `source-audit.json` retains citation-syntax findings, unchanged
canonical slices and exact budget checks; syntax does not prove semantic support.
The later prompt explicitly requires numeric citations and prohibits metadata
objects in answers. No post-generation text repair was added.

| Generation-only timing, seconds | Baseline mean / P50 / P95 | Candidate mean / P50 / P95 |
| --- | ---: | ---: |
| First nonempty delta | 1.025 / 0.729 / 3.005 | 1.046 / 0.798 / 2.870 |
| Complete stream | 3.595 / 2.975 / 8.295 | 3.531 / 2.578 / 10.507 |
| Packing | 0.00424 / 0.00355 / 0.01205 | 0.00513 / 0.00385 / 0.01110 |

There are 18 samples per arm, concurrency 1, alternating order, no warmup,
60-second provider timeout and zero retries. Nearest-rank P95 is the sample
maximum. These timings exclude query embedding, search, reranking and app HTTP.
Background tests, network and provider caching were uncontrolled. No causal
performance gain is claimed. Baseline provider usage was 60,875 input / 4,662
output tokens; candidate usage was 60,765 / 4,023. Billing data is unavailable.
The metadata's extra tokens can displace larger excerpts, so aggregate input
tokens need not increase.

`metrics.json` includes the full inventory with unavailable/not-applicable reasons.
No paid LLM judge was run because its observed claim omissions remain unresolved;
full claim-level quality scores are unavailable. The ranking diagnostics are
unchanged binary gold-span-overlap proxies over top-5 children, not exhaustive
semantic relevance judgments. `answers.jsonl` preserves exact messages, sources,
new packing diagnostics, outputs, deltas, model names and token usage.

The first backend check failed eight tests whose tiny fixture budgets did not
include source metadata. The child fixture now budgets its actual filename and
heading; the Settings wiring fixture budget increased from 24 to 96 tokens.
The production budget remains 4,096. The rerun passed 479 tests, with one skipped;
all logs and metric inventories remain append-only. Browser verification passed
9 tests with the existing UI and lifecycle workflows.

An initial live app smoke took 4.577 seconds to first delta and 6.462 seconds to
completion. It correctly separated the two timing statements and preserved their
source IDs. All 17 files and nine previous conversations were retained, and one
smoke conversation was added. `app-smoke.json` and `app-smoke-metrics.json` record
this separately from the comparison. The final prompt has its own smoke record.

The audit collector used here is [audit.py](../20260924T150609Z-source-metadata-v2/audit.py).
No historical artifacts were overwritten, and no merge was performed.
