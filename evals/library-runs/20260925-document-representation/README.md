# Document representation correction: attribution fixed, acceptance incomplete

The correction supplies both FAQ documents and correctly identifies Admissions as
the page containing the separate-scholarship-application statement. Annotated
comparison evidence coverage improves from **50% to 100%**. All seven answerable
cases now have full annotated-span coverage; named-source compliance passes.

**The frozen full-suite gates still fail.** First pass: **10/11 service completions,
9/11 strict reviewed cases**. One answer times out mid-stream; the FAQ comparison
correctly answers which page, but omits the explicitly frozen second point that
General FAQ lacks this statement. This is an answer-completeness miss, not another
wrong attribution. Do not change that point after seeing the output.

The [one bounded recovery](../20260925-scope-timeout-recovery/README.md) completes
the timeout case correctly. Across both attempts there are **11/12 service
completions**, one timeout, and **10/11 distinct cases with a strict passing
answer**. Every question has a completed answer, but that is not 11/11 strict
quality, first-pass reliability, or a passing full-suite acceptance. No automatic
retry behavior was added, no further paid sampling was performed, and no merge
was authorized.

## Quality and comparison

Same 11 frozen questions, 17 source files, v2 annotations, default GPT-4.1,
omitted reasoning setting, embeddings, prompt, structural chunks, hybrid top-5
and 4096-token budget as the [before run](../20260925-document-scope/README.md).
The corrected code is `b8781cf`; the recovery has identical product-file hashes.
A verified copy of the closed baseline index preserves IDs and chunk topology.
No ingestion, fresh index-quality claim, source refresh or judge calls.

The changed component is document representation during candidate selection and
budgeted source metadata. All supplied claims and associated citations reviewed
in this pass are supported (21 inventoried claim units; some group qualified
clauses supported by the same paragraph). The recovery adds one supported claim.
Codex inspected every raw answer, expected point, cited passage and source label;
this is the implementer's assessment, not independent human ground truth.

| Case | Before | Correction first pass | Separate recovery |
| --- | --- | --- | --- |
| Credit load / weekly effort | Pass | Pass | Not run |
| Independent study / pass-fail | Pass | Pass; 39.05 s | Not run |
| Course in both subject areas | Pass | Pass | Not run |
| General FAQ awards / jobs | Pass | Pass, no Admissions-only policy | Not run |
| Header endpoint scope | Pass | Pass | Not run |
| Message subfield statuses | Pass | Pass; 46.24 s | Not run |
| Unspecified API error | Pass | Incomplete stream; timeout | Pass; 2.89 s |
| Personal approval / supervisor | Pass | Pass | Not run |
| Compare FAQ policy | Wrong attribution; 50% coverage | Correct attribution; 100% coverage; missing explicit absence point | Not run |
| Ambiguous FAQ | Pass | Pass, no provider calls | Not run |
| Missing filename | Pass | Pass, no provider calls | Not run |

[REVIEW.md](REVIEW.md) contains exact answers and supporting quotes/offsets;
[manual-review.json](manual-review.json) preserves both reference versions and
per-point scores. The original awards rubric still loses the optional limited
scholarship-count detail. [comparison.json](comparison.json) retains per-case
before/after/recovery results. Repeated development cases are not held-out accuracy;
provider variation prevents a causal interpretation of single-pass timing changes.

## Performance and reliability

Successful service requests (N=10, including two deterministic clarifications):
mean **10.443 s**, median **3.506 s**, nearest-rank P95 **46.242 s**. First nonempty
answer delta: mean **5.053 s**, median **1.718 s**, P95 **38.993 s**. These fail the
frozen mean <=10 s, complete P95 <=20 s, and first-delta P95 <=10 s thresholds.

Successful generations (N=8): mean **12.531 s**, median **3.187 s**, P95 **46.033 s**;
generation first delta mean **5.798 s**, median **1.147 s**, P95 **38.434 s**.
The slow independent-study request waits about 38.43 s for its first provider
delta; the subfield request starts promptly but takes 46.03 s to finish generation.
The failed API-error attempt separately takes **62.179 s** to terminate at the
service boundary and **61.782 s** in generation (`APITimeoutError`). Failure
latencies remain visible and are not counted as completed responses. The traces
locate delay inside generation but cannot distinguish upstream queuing, provider
processing, network stalls or host suspension. No unsupported root cause claim.

Concurrency is one, SDK retries zero, timeout remains 60 seconds. Measurements use
in-process production streaming service boundaries, include queue/provider waits,
and exclude HTTP/browser overhead. Local platform, exact configuration, index hashes
and monotonic batch duration are in [run.json](run.json). Wall-clock timestamps
span a longer interval than monotonic durations; do not substitute that interval
for service latency or infer production load capacity from this sequential run.

This run uses 18 paid calls: nine query embeddings and nine generations, no judges.
Usage is reported for all embeddings and eight completed generations; the failed
stream has no final usage or resolved-model record. Completed outputs resolve to
`gpt-4.1-2025-04-14`. Maximum observed generation input is 5102 tokens, but the
all-attempt usage gate is unverified because one response lacks usage. Dollar cost
is unavailable, not zero. Including the two-call recovery and the initial 35-call
run, this feature session records 55 paid calls; failed usage remains unknown.

The [complete inventory](METRICS.md) separates selected-child ranking at K=5,
nonexhaustive gold-overlap proxy labels, final source-span coverage, answer quality,
latency, usage and reliability. Per-candidate ranks and budget exclusions are in
[answers.jsonl](answers.jsonl); exact provider inputs/deltas/errors are in
[calls.jsonl](calls.jsonl). Search/fusion is not independently instrumented;
reranking, fresh ingestion and lifecycle operations are not exercised here.

Engineering checks pass; the observed source-selection defect is fixed. Remaining
acceptance work is explicit contrast completeness and the recorded latency/error
gates. Do not keep sampling or broaden implementation merely to obtain a green
aggregate. The user decides whether these limitations are acceptable and explicitly
authorizes any feature merge. See [current readiness](../../../docs/v1/merge-readiness.md).
