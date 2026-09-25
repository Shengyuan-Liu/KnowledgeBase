# Low answer reasoning — 4/5, not accepted

Optional `ANSWER_REASONING_EFFORT` is implemented in `d6a714f`; blank preserves
existing requests. Full backend: 561 passed, 1 skipped. Current local `.env` and
model defaults are unchanged while the user's model preference is pending.

With `gpt-5.4-mini` and explicit `low`, the same five frozen contexts yield **4/5
passing cases**. Header contrast/scope, pass-fail restrictions and both abstention
controls pass. The remaining scholarship answer still attributes an admissions-FAQ
application-process fact to the general FAQ and omits the limited award count.
The overall frozen correctness/citation gates fail; no merge recommendation.

[PLAN.md](PLAN.md), [REVIEW.md](REVIEW.md), [manual-review.json](manual-review.json),
[acceptance.json](acceptance.json), [before metrics](before-metrics.json) and
[after metrics](after-metrics.json) preserve raw outputs and all assessments.
Codex reviewed 21 claim occurrences and 11 reference points; not independent human
validation. Correctness 95.45%; claim support 21/21; associated citation support
20/21; local supporting coverage 20/21. Abstention 2/2, incorrect refusals 0/3.
Every call completed, no error/timeout/retry/invalid ID. Generation mean/P50/P95
1.522/1.568/1.780 s; first delta 0.848/0.812/1.002 s (N=5, median P50, nearest-rank
P95, provider wait included, no service/HTTP timing). Input/output 17,281/739 tokens;
raw usage details retain reasoning tokens. Billed cost unavailable.

Same model revision `gpt-5.4-mini-2026-03-17`; no new ingestion/retrieval or paid
judge. These single historical samples do not establish causal/broad improvements.
A [final high-effort comparison](../20260925-grounding-high/PLAN.md) keeps all other
inputs and gates fixed; it will not discard this failed attempt or relax criteria.
