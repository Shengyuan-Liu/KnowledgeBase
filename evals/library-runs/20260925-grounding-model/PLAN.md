# Existing alternative answer model — controlled verification

The user requested continued correction. Two completed prompt changes have not
resolved the observed attribution/advice failures. Compare the project's already
configured judge-model family `gpt-5.4-mini` as an ANSWER generator against the
[latest GPT-4.1 output](../20260925-grounding-order/README.md). No judge calls are
made. This is one bounded model comparison, not repeated samples until passing.
No local `.env` or checked-in model default changes before results are reviewed.

Same five cases, source text/order, user/developer messages, annotations, runtime
and criteria; change only `answer_model` in this experiment's Settings. Standard
production Responses streaming path, no tools or extra generation stages.
Reasoning effort is not overridden: the [official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
reports `none` as the default and Responses/streaming support. Save actual returned
model revision, usage and timings; do not infer capability from that documentation.
Use existing authorized credentials, timeout 60 seconds, retries zero, concurrency
one, no warmup. Five requests once each. No ingestion, retrieval or embedding.

Apply the same [functional rubric](../20260925-v1-codex-acceptance/PLAN.md) and
[operational gates](../20260925-grounding-order/PLAN.md). All 11 required reference
points fully correct; all factual claims supported; every associated citation
supports its claim, local supporting coverage >=80% overall and at least one
citation per factual answer. Both unavailable cases acknowledge missing details
without invented behavior, personal facts or inapplicable contact advice. Do not
relax the existing scope judgment. Codex reviews every claim including repetitions,
with exact source/answer quotes; Codex is not an independent human reviewer.

Five successful calls, valid citation IDs; generation completion mean <=10 s and
P95 <=20 s, first nonempty delta P95 <=10 s, input <=12000 tokens per request.
Median P50, nearest-rank P95, provider waiting included; no service/HTTP latency.
Complete measurement inventory, inherited retrieval provenance, usage/cost gaps,
concurrency/throughput and failures retained. Different tokenizers/models and
provider-side defaults limit raw token and latency comparisons. Billing is not
inferred from public prices. One known regression set is not broad accuracy.

If this candidate clears all gates, it is eligible for the recommended generation
configuration, with follow-up resolution kept on the previous model unless tested
separately. If it fails, retain the result. Previous attempts remain immutable.
No automatic merge; user explicitly approves merging each feature.
