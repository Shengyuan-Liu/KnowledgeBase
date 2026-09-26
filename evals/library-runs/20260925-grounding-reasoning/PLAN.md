# Explicit answer reasoning — frozen final scoped verification

The existing model comparison improved citation support but left an observed
contradictory yes/no opening and omitted qualification. Add optional
`ANSWER_REASONING_EFFORT` through shared Settings into complete/streaming clients,
API, CLI and evaluations. Blank omits the provider parameter, preserving existing
models. Explicit resolver models keep their own unchanged request; a resolver
that shares the answer client also shares its options. No output repair, second
answer pass, hardcoded source filtering or hidden retry is introduced.

Compare `gpt-5.4-mini` with explicit `reasoning={"effort":"low"}` against
[the provider-default run](../20260925-grounding-model/README.md). Same five questions,
exact messages/order/roles, sources, annotations and all other settings. The
[official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
supports this effort level; actual quality and timing must be measured here.
Freeze all inputs before calls. Each case once, timeout 60 seconds, zero retries,
concurrency one, no warmup; no ingestion, retrieval, embedding or paid judge calls.
Keep all previous failures and any new failures. No retuning or retrying within
this run. Do not claim this selected set is independent release accuracy.

Apply the identical [functional rubric](../20260925-v1-codex-acceptance/PLAN.md):
11 required reference points fully correct with original scope; no unsupported
facts/advice; all associated citations supported; local supporting coverage >=80%
overall plus at least one supporting citation per factual answer; both missing-data
cases appropriately abstain, no incorrect refusal among answerable cases. Inspect
all claims, including extras/repetitions, preserving exact source/answer quotes
and offsets. Missing-information assertions are assessed under abstention. Codex
is the implementer/reviewer, not an independent human.

Five successful calls and valid IDs; generation completion mean <=10 s / P95 <=20 s,
first nonempty answer delta P95 <=10 s, input <=12000 tokens per request. Report
median P50, nearest-rank P95, N=5, provider waits/reasoning included, service/HTTP
excluded. Preserve requested effort and returned token usage including reasoning
when available, resolved revision, throughput, complete metric inventory and
inherited retrieval provenance. Actual billed cost unavailable unless returned.
Single historical samples cannot establish causal or broad quality improvements.

A passing run supports this specific generation configuration, combined with prior
service/UI checks and current engineering checks. It does not pass the unchanged
GPT-4.1 configuration or constitute a fresh full-service acceptance. User model
preference is pending; do not change local `.env` or active model defaults without
resolving that preference. Actual merge always requires explicit user approval.
