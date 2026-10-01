# Frozen live PDF development acceptance protocol

Frozen before ingestion and answers on 2026-09-27, code `3106e06`, branch `v2`.
Use the five byte-identical PDFs in `frozen-cases.json`: paper, lecture, technical,
financial and dense statistical reports. Original pages were rendered and reviewed
before freezing 16 questions, including a two-turn sequence. This is development
acceptance on previously seen material, not a held-out release evaluation.

Compare A (`single`) and D (`planned`, sufficiency enabled) through the real local
HTTP SSE endpoint. Keep the same index, parser/model revisions, retrieval and
packing settings, original questions and source scopes. Use current `.env` models
and settings, including its enabled reranker; do not edit `.env`. Record resolved
settings. Use an isolated ignored data directory and loopback server. Perform one
pass, sequential concurrency 1, alternating arm order by case; follow-ups reuse
their own arm's preceding conversation. No retries; failures remain in denominators.
No tuning during the first pass. Any repair requires a new run directory.

This is a whole-product A/D comparison. The base answer instructions and model
are identical. D additionally passes its implemented fallible assessment guidance
and may deterministically abstain; A has no assessment. This explicit deviation
from the proposed identical-prompt retrieval ablation prevents attributing answer
changes solely to extra retrieval. B/C and passive-assessor ablations are deferred.
Planning is live and stochastic; one pass does not estimate variance.

Capture SDK call inputs, model/response IDs, raw structured outputs, final streamed
responses and provider usage without credentials. Streaming usage is read from the
actual `response.completed` event, not estimated from character counts. Follow
[official streaming event documentation](https://developers.openai.com/api/docs/guides/streaming-responses).
Record request start to first nonempty final-answer delta and HTTP completion
separately. Record planning, assessment, retrieval, rerank, packing, parsing and
provider timings where available. Include startup/model loading separately and
first-call cold effects. Real billed cost is unavailable without billing records;
do not call an estimate a bill. Cache-token counts remain provider observations.

Quality review: Codex (model), not an independent human judge, inspects every
answer against frozen original-page facts and its exact supplied/cited sources.
Retain an answer-claim inventory with correct/incorrect/partial labels, supported/
unsupported labels, reference-point coverage, relevance, citation support and
coverage, and per-case notes. Expected fact correctness and completeness use
0, 0.5 or 1 per point; missing-information requirements are scored separately.
Fully unanswerable cases have no retrieval-recall denominator. A fully abstaining
response on an answerable case counts as incorrect abstention. Partial cases must
answer supported points and explicitly identify missing ones. No semantic scores
are inferred from valid citation IDs or well-formed checker output.

For retrieval, map frozen original-page anchors to canonical spans after ingestion,
retaining omitted/unmatched anchors as parser failures. Report Recall@5 as gold-fact
anchor coverage by the first five selected child candidates, Precision@5 as the
fraction of those five touching an annotated fact anchor (denominator five even
when fewer results), Hit Rate@5, MRR@5, and binary NDCG@5 over annotated relevant
children in the frozen index. Labels cover the frozen anchors, not every potentially
relevant paraphrase; these are benchmark-anchor diagnostics and conservative
precision/ranking judgments, not exhaustive semantic relevance scores. Preserve
per-query candidate/fusion/rerank order and final selection separately; do not
attribute selected-stage scores to raw vector search. Final semantic evidence
coverage is reviewed separately, including PDF supplements and table headers.

Development acceptance gates (frozen, provisional): all five uploads become Ready
with correct original bytes/page identity; all 32 requests finish without provider,
schema or controller error; zero invented cited facts; no loss of mean reference-
point correctness or final fact coverage versus A; both unanswerable cases abstain;
all original links/history/delete checks pass. Report missed gates rather than
silently accepting them. Quality/performance remain separate. No latency or cost
release threshold is claimed before observing development measurements. Genuine
contradictory-source accuracy is unavailable here: the labeled comparison is a
period difference, not a fabricated contradiction. OCR/figure/formula recognition
is out of scope; the screenshot case tests limitation behavior only.

Retain every attempt and the complete measurement inventory. A successful run
or a favorable aggregate does not authorize acceptance or merging into `main`.
