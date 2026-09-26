# Source scope correction — fixed-context verification

Freeze before the first new provider call. Production change: four shared prompt
lines require source-supported quantifiers and retain explicit restrictions.
No answer repair, retrieval change or new default setting.

Replay these five existing questions exactly once with their original user and
source messages: `accept-beta-header-scope` (observed failure),
`accept-independent-passfail` (explicit exclusive restrictions),
`accept-awards-jobs` (limited awards and no guaranteed job),
`accept-unspecified-api-error` and `accept-personal-study-approval` (two abstention
controls). All are now development/regression cases, not new held-out acceptance.
Selection precedes results; retain every attempt, do not retry for a better answer.
No ingestion, embedding, retrieval or paid judge calls. Use the baseline GPT-4.1
configuration with 60-second timeout, zero retries, concurrency one, no warmup.
Preserve actual resolved model, usage, deltas, latency and provider errors.

Use the unchanged manual protocol and source-support/citation gates in
[the prior acceptance plan](../20260925-v1-codex-acceptance/PLAN.md): every required
fact correct with original scope; no unsupported facts/advice; both missing-data
cases acknowledge the limit; all associated citations support their claims;
overall locally supported claim coverage >=80%, at least one citation per factual
answer; valid source IDs. Inspect all claims, including extra claims and repeats.
Use explicit claim quotes, source quotes and offsets, reference-point scores and
per-case decisions. Reviewer is Codex, the implementer, not an independent human.
Retain the baseline's 7/8 failure. Compare the SAME selected five baseline answers
with new answers under the same protocol; do not label this a fresh 8/8 service run.

Generation-only completion mean <=10 seconds, P95 <=20 seconds, first nonempty
generation delta P95 <=10 seconds, input <=12000 tokens per request. These are
sanity gates, not the original end-to-end service latency measurements. Record
median P50 and nearest-rank P95. Ingestion, retrieval timings and HTTP latency are
not applicable to this replay; source provenance and rankings are inherited.
Billed cost remains unavailable if the provider does not return it. No inference
of causal latency gains from a single historical comparison.

If all five pass, combine this narrow correction evidence with the prior service
and engineering checks to recommend the existing default functional v1 scope,
with experimental options still opt-in and broad quality validation unclaimed.
If any fail, preserve and disclose it. Actual merge still requires user approval.
