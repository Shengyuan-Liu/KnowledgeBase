# Codex Functional Acceptance — Frozen Before Outputs

The user asked Codex to perform acceptance rather than require the user to conduct
all manual checking. Codex will inspect actual answers and sources and make a
functional merge recommendation. This does not turn Codex into an independent
human reviewer. Broader independent validation remains a disclosed limitation,
not a request for the user to do all verification before Codex can give a verdict.

## Frozen scope

Eight new questions, six answerable and two unanswerable, on the existing 17-file
frozen corpus. No question exactly repeats the previous 24, and no result will be
used to adjust this run's questions, criteria, prompt or settings. The corpus and
failure categories are familiar; this is not independent held-out accuracy.
`cases.json`, `corpus.json` and `freeze.json` preserve exact reference spans/hashes.

Use the checked-in functional defaults: structural parent-child 512/1536 tokens,
hybrid BM25/vector, route limit 20, RRF k=60, top K=5, parent-then-child packing,
4096 evidence tokens, local reranking disabled, GPT-4.1 and embedding-3-small.
Fresh isolated index. Sequential streamed service requests, timeout 60 seconds,
zero SDK retries, no paid judge calls. Record ingestion, rankings, supplied text,
all deltas, errors, timing and provider usage. No `.env` or user index changes.
Existing green engineering/UI tests are reused because production code is unchanged.
The service run includes persistence but excludes browser/HTTP transport.

## Pass criteria and review protocol

Freeze these before generation. They are functional acceptance thresholds informed
by earlier development observations, not universal quality guarantees:

1. All eight requests complete without errors/timeouts/retries. Source excerpts
   match the canonical source offsets and stay within the 4096-token formatted
   evidence budget. No invalid citation IDs. No source/reference leakage.
2. Every required fact for each answerable question is present in supplied evidence
   and answered correctly, preserving conditions, exclusions and source identity.
   Assess source-span metrics separately; whitespace-only annotation gaps do not
   constitute missing facts. No major factual error or unsupported factual advice.
3. Both unanswerable questions explicitly acknowledge the information limit without
   inventing a status, error payload, personal decision or supervisor. An answer
   saying only that a field is unsupported must not infer a particular failure
   behavior. Record full/partial abstention separately from incorrect abstention.
4. Inspect all factual claims, including unsolicited claims and repetitions.
   References/headings are not substantive claims unless they assert a fact.
   Claim support is supplied-source support, not agreement with the reference.
   Cite exact answer quotes and source quotes with source IDs/offsets. A local
   citation is in the same sentence/list item or same prose paragraph, semantically
   associated; a heading/final summary does not cover separate list items. Code
   citations require nearby comments without changing executable behavior.
   All assessed citations must support their associated claim; at least 80% of
   factual claim occurrences overall must have a local supporting citation, and
   every factual answer must have at least one supporting citation. Missing local
   citations remain defects even if the threshold passes. This 80% threshold is
   based on the prior 81.71% development result and represents an explicitly limited
   functional release, not complete citation coverage or a v11 comparison.
5. Service completion mean <=10 seconds and P95 <=20 seconds; first nonempty answer
   delta P95 <=10 seconds. These are coarse local sanity limits from prior runs,
   not a load-capacity claim. P95 is nearest-rank; concurrency one, no warmup.
   Provider generation input <=12000 tokens per request. Record actual input/output
   usage; billed cost may remain unavailable. Ingestion completes within 120 seconds.
6. Give a per-question result and overall pass/fail without adjusting criteria
   after outputs. If a required gate fails, recommend against unconditional
   acceptance, identify the specific blocker, and retain this run as a failed
   acceptance attempt. Do not silently repair outputs or re-run until passing.

Manual reviewer: Codex, author of the tests and implementation. This is a labeled
model-assisted audit, not independent human review. Answer correctness and
completeness use required reference points; faithfulness/citation metrics use the
recorded claim inventory. Relevance is 2 fully responsive, 1 partly/extraneously
responsive, 0 off-topic. No aggregation can hide a major factual error.

The existing independent-human-review gate remains relevant to claims of broader
semantic validation. It does not prevent providing the Codex acceptance requested
by the user or recommending a functional merge with explicit limits. Actual merge
still requires explicit user approval.
