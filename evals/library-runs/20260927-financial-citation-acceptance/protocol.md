# Financial citation follow-up: frozen acceptance protocol

Frozen before calls at product commit `ae59147`, branch `v2`, on 2026-09-27.
Run exactly the three questions in [frozen-cases.json](frozen-cases.json) once in
each of `single` and `planned` mode: six sequential HTTP/SSE requests, alternating
mode order by question, no automatic reruns and zero provider retries. Compare
with the immediately preceding [financial acceptance](../20260927-financial-acceptance/README.md),
which completed six requests but had one uncited factual bullet (13/14 coverage).

Use its unchanged expected facts and paragraph/bullet review rules. Each separate
factual item needs its own supporting inline citation, including multiple items
from the same source. Check each requested value against the correct three- or
twelve-month period ending September 28, 2024, and applicable units. A valid source
ID is not sufficient proof. Review actual supplied/cited passages and original
page 1, including table headers and units. Page-4 income reconciliation is not
sales evidence. Preserve model choices, historical scores, errors and disagreements.
Reviewers are Codex agents, not independent humans; no paid judge is called.

Clone the inactive prior isolated data directory while holding its ownership lock.
Verify copied file hashes, all five original PDFs, extractions, 621 child records,
parents and vector storage against the frozen source and prior accepted preparation.
Do not reparse, rechunk or regenerate embeddings. The previous historical vector
restoration limits remain documented, but this immediate comparison reuses exactly
the same persisted vectors. A new directory isolates conversation writes from the
prior run and production data. Existing conversations are cloned but each test
begins a fresh conversation with the original file scope.

Keep the prior models/settings: GPT-4.1, text-embedding-3-small, K=5, hybrid retrieval,
BGE reranker and recorded revision/device, 4,096 evidence tokens, three rounds/six
queries, 8,192 planner input tokens and 16,384 answer input tokens. Timeout is 180
seconds and retries zero. Preserve `.env`; use the already authorized existing key.
Record resolved settings/models/revisions, exact SDK inputs/outputs, rankings,
budget exclusions, raw assessments, supplied sources, stream events and saved
history. Hold product code, prompts and budgets fixed during all six requests.
Do not tune or repair answers after seeing outcomes.

The changes under test are current-source navigation hints, a final repeated-citation
format example, and separate application-attached table context. For the three
planned requests, inspect selected references and attached table context separately.
Attachments do not prove semantic sufficiency or count as model-selected support.
They must retain exact source locations and qualifier text; saved history must
preserve both. Review this separately from final-answer quality.

Scoped gates: all six requests complete; all requested points are correct and
complete; all factual groups have supporting inline citations with correct periods
and units; zero incorrect abstentions or fabricated cited facts; persisted answer,
sources and retrieval metadata match the response. Report each gate separately.
All questions are answerable; appropriate abstention on unanswerable cases is not
applicable. These are reused development cases, not held-out general accuracy.
Stochastic plans/rankings may vary despite identical data/settings; disclose actual
differences. Passing this subset does not establish overall v2 acceptance or
authorize a merge into `main`. Dense-table and broader retrieval limits remain.

Record all 20 measurement-policy metrics with values or explicit applicability
reasons. Measure first nonempty answer delta and HTTP stream closure separately,
including failures. Record stage counts, means/P50/P95, query and answer token
usage, reliability and sequential throughput. Startup/model-loading/cache scope
must be explicit. Billed cost and isolated provider queue time remain unavailable
unless supplied. Preparation is an offline clone/verification, not ingestion
performance. Save every attempt append-only in this new run directory.
