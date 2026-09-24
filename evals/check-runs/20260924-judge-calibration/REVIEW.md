# Judge calibration delivery review

This change adds a source-blind inventory audit and a reproducible calibration
command. It improves the measured judge behavior but does **not** establish a fully
reliable evaluator. The final fixed calibration set has **15/16 matching judgments**;
one internally contradictory review remains pending. No failed result was repaired
or relabeled as passing. Implementation and records remain on `v1`; no merge is
authorized by these results.

## Delivered behavior

The judge now extracts assertions, audits extraction using only the original answer,
then scores evidence support. It preserves alternatives and restrictive qualifiers,
distinguishes conjunctions from disjunctions, treats documented procedures as facts,
and resolves nested fields in context. Source lead-ins describe answer organization;
they do not require a source to attest to the answer's production history. Specific
source-attributed facts still require support.

`make eval-calibrate` runs 16 frozen development fixtures and reports agreement,
correct-answer rejections, known-error detection, refusal behavior, pending reviews,
latency, actual usage and reliability. It returns nonzero on a mismatch or pending
review after saving results. `make eval` uses the same current judge for the full RAG
benchmark. The configured judge remains `gpt-5.4-mini`; default/local reasoning is
now `high`, with a 180-second timeout per call and four concurrent reviews. There
are three calls per complete judgment; the timeout is not a whole-review deadline.
The RAG answer model remains `gpt-4.1`.

## Calibration result and remaining gate

The final [16-case run](../../calibration-runs/20260924T193931Z-14f32e71-claim-inventory-v10/README.md)
contains ten correct answers, five known errors and one appropriate refusal.
All ten correct answers and the refusal match their labels. Four known-error
reviews match; one is pending. For that invented personal schedule, the judge
correctly identifies unsupported facts but returns both `abstains=false` and
`appropriate_abstention=true`. The validator rejects the contradiction. It is
neither an accepted wrong answer nor a successful complete judgment.

Compared on the same original 12 corrected fixtures, protocol 4/medium has 7/12
matching judgments and protocol 10/high has 11/12; the four added regressions pass.
Prompts, audit structure and reasoning effort changed, so the improvement cannot
be attributed to a single change. These are Codex-authored development labels,
not independent human annotations or held-out accuracy.

Medium and high were also compared under protocol 9 on the same 14-case snapshot:
agreement was 12/14 versus 14/14; average review time was 9.80 versus 18.81 seconds,
and total provider tokens were 73,099 versus 92,911. Subsequent real-answer inspection
found semantic errors despite the 14/14 result, motivating protocol 10's added
source-leadin and nested-field cases. A small passing set does not prove reliability.

All intermediate runs, failures, two fixture corrections, raw model outputs and
code snapshots are retained. See the [development record](README.md) and
[full experiment comparison](experiment-comparison-final.json). Audited summaries
only correct reporting provenance and error-detection accounting; raw semantic
scores remain unchanged.

## Saved-answer regrade

The [final 18-answer regrade](../../calibration-runs/20260924T194004Z-1a80463c-saved-answers-high/README.md)
uses byte-identical answers and evidence from the original run. Only judgments are
fresh. Original protocol 4 produced 15/18 machine-valid reviews; protocol 10/high
produces **17/18**. The original waiver, personal-schedule and SDK-installation
inventory failures are resolved in this pass. The mathematically-intensive
prerequisite qualifier is preserved, and source-leadin/nested-field false negatives
seen in protocol 9 no longer appear in the final raw reviews.

The remaining pending real case is `msds-pathbreaker-fall2027`: extraction drops the
answer's explicit "not mandatory" qualifier, and the source-blind audit correctly
stops scoring. Full-set strict pass rate is therefore unavailable. This is not a
wrong answer being silently accepted or a repaired judgment.

Semantic inspection still finds a false-negative risk in `msds-gpa`: the judge
again treats "main academic progress requirements" as an unsupported official
priority claim, contrary to the editorial-emphasis rubric. The `msds-credits`
assessment also flags "other factors" beyond course availability; its hedge and
scope warrant review. Raw scores are retained. See
[per-case claims and verdicts](saved-answer-inspection-final.json). Machine validity
does not resolve these semantic concerns, and they prevent a claim that calibration
is fully successful.

| Measurement | Original protocol 4 / medium | Final protocol 10 / high |
| --- | ---: | ---: |
| Machine-valid reviews | 15/18 | 17/18 |
| Judge mean duration | 32.58 s | 62.40 s |
| Judge P50 | 25.93 s | 49.45 s |
| Judge P95 | 92.25 s | 189.36 s |
| Judge API calls | 36 | 53 |
| Input tokens | 221,818 | 238,315 |
| Output tokens | 106,163 | 239,316 |
| Total tokens | 327,981 | 477,631 |
| API errors / timeouts / retries | 0 / 0 / 0 | 0 / 0 / 0 |

Durations include all completed attempts, including pending ones, and exclude
waiting for a worker. P50 is the median; P95 is nearest rank. The final four-worker
batch took 301.66 seconds. Its mean inventory/audit/assessment durations were
13.34/5.83/45.77 seconds; assessment has N=17 because the failed audit stops it.
RAG latency was not remeasured and is not included in these judge durations.
Every returned usage object is retained; billed dollars remain unavailable.

## Verification and interpretation

Backend checks: **515 passed, 1 skipped**, 14.46 seconds, with one existing dependency
deprecation warning. See [the final log](backend-6.log) and
[its complete offline metric inventory](backend-6.json). Unit checks verify that
the inventory auditor cannot see sources/reference labels, contradictory reviews
remain unscored, expected negative-verdict classification is separate from error
detection, reports survive mismatches, and configuration overrides remain effective.

No new retrieval, generation, ingestion or lifecycle workload was run. Saved answer
bytes and supplied source spans remain unchanged; any change in quality scores is
judge behavior, not improved or degraded RAG performance. Historical RAG latency and
usage in replay summaries are explicitly reused observations. Billed dollars are
unavailable. Some four-worker batches overlapped; timing differences include provider
load and cache variation.

Same-line citation scope still undercounts citations placed after lists. Final
machine-validity and semantic correctness are different concepts. The remaining
calibration failure must stay visible; this delivery does not declare the judge
fully calibrated or authorize moving past the user's acceptance/merge decision.
