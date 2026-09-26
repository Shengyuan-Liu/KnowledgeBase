# Named-source and table-status correction — frozen verification

The user requested correction after the failed source-scope verification.
The completed production change instructs generation to use the named document,
match each claim to its supporting excerpt before assigning citations, omit
unneeded facts from other documents, and quote table status cells without adding
scope from the question or neighboring rows. No source filtering, second model
pass, output repair or settings change is introduced.

Replay exactly the same five questions and original user/evidence messages from
[the preceding attempt](../20260925-source-scope/README.md), once each, after scoped
engineering checks. Preserve every output; do not retry to obtain a passing one.
The corpus, annotations, evidence order, source IDs and model configuration are
fixed. GPT-4.1, timeout 60 seconds, no SDK retries, concurrency one, no warmup.
Five generation requests only; no ingestion, embedding, retrieval or paid judge.
Existing user-authorized API credentials are reused without changes or disclosure.

Keep the original [functional review protocol](../20260925-v1-codex-acceptance/PLAN.md):
all required points fully correct with supported scope; no unsupported claims or
advice; both unavailable-information cases explicitly abstain without inventing
personal facts or error payloads; every associated citation supports its claim;
local supporting citation coverage >=80% overall and at least one citation per
factual answer. Review all factual claim occurrences, including repetitions and
unsolicited facts, with exact answer/source quotes and source offsets. An uncited
claim can be supported in the context but fails local citation coverage. Codex is
the implementer/reviewer, not an independent human. These are development cases,
not a held-out release population.

In particular, do not relabel the earlier conservative header-scope judgment to
make this run pass. Assess the new wording against the same requirement. The
separate wrong-FAQ attribution is a definite failure if repeated, regardless of
the header interpretation. Retain both prior failed attempts unchanged.

Operational gates: all five requests succeed, valid citation IDs; generation
completion mean <=10 seconds and nearest-rank P95 <=20 seconds; first nonempty
generation delta P95 <=10 seconds; generation input <=12000 tokens per request.
Report median P50, nearest-rank P95, sample counts, provider revision/usage,
concurrency/throughput and complete metric inventory. Generation timings include
provider waiting, exclude service/HTTP work. Inherited retrieval observations are
provenance, not fresh measurements. Billed cost unavailable unless returned.
No causal timing or quality claim from single historical samples.

If all five pass, the corrected default functional scope may be recommended for
merge together with the existing service, backend and UI checks. State that this
is targeted regression evidence, not a fresh full-service 8/8 run or a guarantee
of universal semantic correctness. Experimental options remain opt-in. If any
fail, retain and disclose them. Actual merge requires explicit user approval.
