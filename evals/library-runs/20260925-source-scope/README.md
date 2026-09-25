# Source-scope prompt verification — failed

A four-line shared prompt instruction was added and committed as `8226389` after
68 relevant tests passed. The completed change was tested with five saved-context
provider requests, exactly once each. **3/5 pass, versus 4/5 on the same selected
baseline questions. Do not recommend unconditional v1 merge from this result.**
This is a failed targeted verification, not a new full-service acceptance run.
The prior [7/8 service run](../20260925-v1-codex-acceptance/README.md) is unchanged.

## Changes and controls

Only the developer instructions changed: require evidence-supported quantifiers,
keep explicit restrictions/exceptions, and avoid universalizing a table status.
There is no output repair or word blacklist. Tests preserve the original source
text, including explicit `Only`, across complete and streaming generation paths.

The [plan](PLAN.md), selection, checksums and prompt were frozen before new calls.
Original user messages, evidence text/order, source IDs, rankings and references
are identical to the baseline. No ingestion, embedding, retrieval or paid judge
calls. Existing `.env` credentials reused; no user configuration/index changed.
GPT-4.1 resolved to `gpt-4.1-2025-04-14` in both runs; timeout 60 seconds, retries
zero, concurrency one, no warmup. Provider load/cache variation is uncontrolled.
Each prompt has only one sample per selected question; differences are descriptive,
not proof the prompt change caused a regression or a latency change.

## Findings

| Case | Before | After | Finding |
| --- | --- | --- | --- |
| Header behavior | Fail | Unresolved/fail | `always ... on all endpoints` became `in both cases`; exact universal wording disappeared, but endpoint scope is still inferred from `Ignored`. |
| Independent study / pass-fail | Pass | Pass | Maximum credits, explicit `only`, exclusion and concentration allowance retained. |
| Scholarships / jobs | Pass | Fail | A true statement from admissions FAQ [1] is cited as general FAQ [2], followed by an unsupported all-general-FAQ attribution. |
| Unspecified API error | Pass | Pass | No invented HTTP status or JSON error body. |
| Personal study approval | Pass | Pass | No invented approval status, supervisor or unsupported contact advice. |

The header verdict is deliberately conservative and debatable: the table does
not enumerate version-header behavior by endpoint. This is not proof of contrary
real API behavior. Even accepting that interpretation would yield 4/5, with the
wrong-FAQ citation still independently failing the frozen associated-support gate.
The extra scholarship fact exists in the supplied context; the failure is its
citation/source attribution, not fabrication of the policy itself.

Codex reviewed all answers and every inventoried factual claim against supplied
source text. Codex is also the implementer and is not an independent human reviewer.
[REVIEW.md](REVIEW.md) contains unedited answers, exact claim/source quotes, offsets
and findings. [manual-review.json](manual-review.json) retains all 30 claim occurrences
and 11 reference-point scores. Missing-information statements are assessed under
abstention. Citation association uses the original paragraph/list-item protocol,
not v11 same-line scoring; no cross-protocol aggregate comparison is claimed.

## Quality and operations

| Metric | Same five baseline cases | After change |
| --- | --- | --- |
| Reference-point correctness | 95.45%, 11 points | 95.45%, 11 points |
| Required points present | 11/11 | 11/11 |
| Supported factual claims | 25/26, 96.15% | 28/30, 93.33% |
| Supported associated citation pairs | 40/41, 97.56% | 35/37, 94.59% |
| Claims with local supporting citations | 24/26, 92.31% | 27/30, 90.00% |
| Appropriate abstention | 2/2 | 2/2 |
| Incorrect abstention | 0/3 | 0/3 |

After-change generation completion: mean 2.465 s, P50 2.261 s, P95 3.662 s.
First nonempty generation delta: mean 1.019 s, P50 0.873 s, P95 1.713 s.
N=5, median P50 and nearest-rank P95, provider waiting included. These are
provider-generation measurements, not service/browser response times. All five
requests succeeded, with zero errors/timeouts/retries and valid citation IDs.
Provider usage: 16,621 input and 737 output tokens; largest input 4,569.
Actual billed cost is unavailable, not zero. No local inference model was loaded.

[Before metrics](qualified-before-metrics.json) and [after metrics](after-metrics.json) retain
the complete inventory, reasons for unavailable/not-applicable measurements,
concurrency/throughput, inherited ranking/coverage provenance and raw artifact
locations. The inherited retrieval figures are not fresh retrieval measurements.
[acceptance.json](acceptance.json) records every gate and per-question transition.
[Engineering records](../../check-runs/20260925-source-scope/README.md) distinguish
mocked checks from live quality. No same-prompt retry, repaired response or changed
acceptance criterion is used to make the failed result pass.

The prompt now states the intended scope more explicitly, but its behavioral fix
is not verified. The next grounding work must address exact table-status scope
and named-source/citation identity. Keep experimental retrieval settings opt-in;
no broader feature is needed and no merge has been performed.
