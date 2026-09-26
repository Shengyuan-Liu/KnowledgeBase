# Codex v1 Functional Acceptance

**Result: 7/8 cases pass; unconditional acceptance fails one source-scope check.**
Codex completed the requested acceptance, including all answer/source checks.
The blocker is a specific output qualification, not a requirement for the user to
do Codex's verification work. No production code or answer was changed, no
failed result was discarded, and no merge was performed.

The [plan and criteria](PLAN.md) were committed at `23a7262` before any result.
Eight new questions use the existing familiar 17-file corpus. This is a small
functional acceptance set authored and reviewed by Codex, not independent human
review, independent held-out accuracy, or proof of broad quality improvement.

## Results

| Case | Result | Observation |
| --- | --- | --- |
| Course load and weekly effort | Pass | 9 / fewer than 9 credits; 10–15 hours with prerequisite condition |
| Independent study and pass/fail | Pass | Six-credit cap, elective exclusion, required-course restriction and concentration allowance preserved |
| Course in both subject areas | Pass | DS-GA 1012 appears in both lists with correct title |
| Scholarship and job qualifications | Pass | Competitive/limited awards and no guaranteed job; extra application-process statement is supported by the admissions FAQ |
| Header scope | **Fail** | Correct base statuses, but `anthropic-version` is expanded to “always ... on all endpoints” |
| Nested message fields | Pass | Distinguishes text citations, tool-use ID and tool-result error flag |
| Unspecified API error | Pass | Does not invent an HTTP status or JSON error body |
| Personal study approval | Pass | Does not invent approval/rejection, supervisor or a contact |

Read the complete answers and supporting excerpts in [REVIEW.md](REVIEW.md).
`manual-review.json` contains 38 factual claim occurrences with exact answer/source
quotes, offsets, citation associations and reasons. `acceptance.json` applies the
unchanged gates; `reviewed-metrics.json` contains the complete metric inventory.

### Blocking qualification

The supplied table says `anthropic-version | Ignored`. The answer says:

> For anthropic-version, it is always ignored (not used) on all endpoints [2].

The base status matches. The universal endpoint guarantee is not established by
the supplied excerpt. Under the frozen scope-preservation and citation-support
rules, Codex marks the stronger claim insufficient and the affected reference
point partly correct. **This is not a verified claim that the actual API behaves
differently.** It is a conservative source-support judgment, with the raw text
retained for review. No external API behavior was used to override the frozen
source. The appropriate wording would simply report the table's `Ignored` status.

The extra no-separate-scholarship-application statement was separately checked:
it is explicitly stated in the retrieved admissions FAQ. It was not mislabeled
as an invention merely because the general FAQ does not include that sentence.

## Quality and operational observations

- All 8 service requests completed; all 33 provider calls succeeded, zero retries.
- All annotated evidence spans for the 6 answerable questions were supplied: 100%
  character coverage and fully covered-span fraction. Every excerpt matches its
  canonical source offsets and fits the 4096-token formatted evidence budget.
- 17 reference points fully correct, 1 partly correct, none missing: 97.22%
  micro-average correctness, 100% attempted completeness. All required points
  must be fully correct to pass the frozen gate; the aggregate cannot hide failure.
- Claim support: 37/38 (97.37%). Associated citation support: 52/53 (98.11%).
  Local supporting citation coverage: 36/38 (94.74%). The uncited introductory
  header comparison and the unsupported universal qualification remain visible.
- Appropriate abstention: 2/2. Incorrect abstention on answerable questions: 0/6.
- These are Codex assessments, not ground truth. The preregistered manual citation
  protocol uses paragraph/list-item scope and micro-aggregation; do not compare
  these figures directly to historical v11 scores.

| Service timing, seconds (n=8) | Mean | P50 | P95 |
| --- | ---: | ---: | ---: |
| First nonempty answer delta | 1.045 | 1.092 | 1.244 |
| Complete response | 2.181 | 2.068 | 3.021 |

Timing starts at the in-process streamed service and includes persistence at
completion; it excludes HTTP/browser transport. P95 uses nearest rank. Concurrency
is one, no warmup, host/provider load uncontrolled. Sequential throughput is 0.458
requests/s over the recorded 17.469-second question batch, not a load-capacity claim.

Fresh ingestion: 17 files, 92 children, 7.592 seconds, 2,418,852 index bytes.
Provider usage: ingestion 26,199 tokens; query embedding 268; generation 27,386
input and 913 output tokens. Maximum generation input is 4706 tokens, below the
frozen 12,000-token limit. Actual billed cost is unavailable. No paid judge calls
or local reranking model load occurred. This run does not repeat update/deletion
or browser lifecycle checks; their existing passing records remain linked below.

The tested configuration is the checked-in default: structural parent-child,
hybrid retrieval, child scoring, reranking disabled, 4096-token evidence budget.
Semantic chunking and whole-parent reranking are still opt-in experimental options.
`.env` and the user's existing indexes were unchanged.

## Recommendation

Engineering/operational gates pass, with prior backend 554 passed / 1 skipped,
frontend 40 passed, browser 10 passed and successful production build retained in
[the engineering record](../../check-runs/20260925-retrieval-coverage/README.md).
No production code changed since those checks, so no redundant suite or full
paid benchmark was run.

Do not describe this run as passing the frozen semantic acceptance criteria.
The next work is a narrowly scoped generation qualification fix and targeted
verification. This set is now observed development evidence; do not tune on it
and continue calling it held-out. Further independent human review can strengthen
confidence but is not a substitute for the Codex audit already completed here.
The user retains final merge authority.

Ranking diagnostics use K=5 native child units and binary overlap with the frozen
source annotations; relevance labels are incomplete, particularly for precision.
`stage-metrics.json` separates vector/BM25 candidate windows, RRF fusion, selected
children and final supplied-source coverage. No reranking stage was exercised.
Use `qualified-metrics.json` as the final inventory: it preserves the reviewed
summary and explicitly marks disabled reranking latency not applicable.
