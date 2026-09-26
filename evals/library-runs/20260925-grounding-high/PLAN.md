# High answer reasoning — final bounded comparison

Low reasoning passes four cases but still mixes FAQ attribution. Compare the
same already implemented option at `high`, supported by the model and already
used elsewhere in the project's judge configuration. This is answer generation,
not a paid judge. Change only `answer_reasoning_effort` from low to high; same
`gpt-5.4-mini`, exact question/evidence/developer messages, order, corpus, references,
SDK path and all other settings as [the low-effort run](../20260925-grounding-reasoning/PLAN.md).
Freeze before calls. Five requests once each, timeout 60 seconds, retries zero,
concurrency one, no warmup. No retrieval, embedding, ingestion or output repair.

Use the identical original functional rubric and five-case operational gates:
all 11 reference points fully correct with source-supported scope, all factual
claims supported, every associated citation supports its claim, >=80% local
supporting citation coverage overall with at least one citation per factual
answer, correct abstention on both unavailable cases and no incorrect refusal
on the three answerable cases. No unsupported contacts or personal advice.
Codex reviews all claims including extras/repeats with exact answer/source quotes
and offsets; not independent human review. Do not change judgments of prior runs.

Require five successful calls with valid IDs; generation mean <=10 s/P95 <=20 s,
first nonempty answer delta P95 <=10 s, input <=12000 tokens per request. Report
median P50, nearest-rank P95, N=5, provider wait/reasoning included, no service/HTTP
measurements. Preserve requested effort, returned reasoning-token usage, revision,
all failures, complete metric inventory and inherited retrieval provenance.
Billed cost unavailable unless returned. Single known regression samples are not
held-out accuracy, causal effect estimates or guarantees of model compliance.

This is the last configuration comparison in this correction session. If it still
fails, record the remaining blocker; do not continue sampling other settings or
relax the gates. If it passes, recommend this specific candidate configuration,
not unchanged GPT-4.1, together with existing service/UI and current backend checks.
The user's model preference is pending; local `.env` and active defaults remain
unchanged until it is resolved. No automatic merge.
