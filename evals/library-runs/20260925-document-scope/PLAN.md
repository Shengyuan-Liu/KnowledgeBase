# Document-scope feature acceptance

Freeze this plan before provider calls. Evaluate the completed document-scope
feature with the current default GPT-4.1, reasoning omitted, structural
parent-child 512/1536, hybrid top-5, 4096-token packing and reranking disabled.
No daily .env/model change. Same 17 frozen source files, hashes and source-span
labels as the original eight-case service acceptance. No source website refresh.

## Workload and comparison

Run the same eight service questions once each, plus three feature controls:
comparison of both FAQs, ambiguous FAQ name and a nonexistent filename. The two
clarifications should not invoke embeddings or generation. Fresh isolated index;
17 ingestion requests, up to 9 query-embedding and 9 answer-generation requests,
zero paid judges, zero retries. Sequential, 60-second provider timeout, no warmup.
Stop on recorded failure; do not change prompts, models or annotations to sample
until pass. Keep all raw events, answers, calls, errors and measurements.

The previous question-aligned annotations from 20260925-answer-focus apply to the
eight retained cases. Preserve original references separately; they differ only
in two awards points that demanded unrequested details. Compare the five shared
cases to that run (same answer prompt/model/settings; actual evidence now changes
because document scope precedes ranking). The original eight-case service run
supplies historical full-pipeline retrieval/timing data but uses an older prompt;
it is not an isolated causal comparison. Both old results remain unchanged.
Fresh random file IDs, vector index construction, provider variation and historical
single samples limit attribution. Use stable file/source spans for coverage,
never compare UUIDs as relevant units. No new held-out accuracy claim.

## Gates fixed before output

Codex manually inspects every answer, required point, extra/repeated factual claim,
associated citation and source scope. Record exact answer/source quotes and offsets.
The same agent implements and reviews; this is not independent human review.
All question-aligned reference points must be fully correct with supported scope;
all factual claims and associated citations must have source support. Local cited
claim coverage >=80% overall with at least one supported citation per factual
answer; claim-free abstentions/clarifications are exempt. Preserve necessary limits.
English explanatory text is required; names/code identifiers remain as written.

The two personal/error questions must withhold unavailable specifics. The two scope
controls must clarify without answering from other files or making provider calls.
No incorrect refusal on the seven answerable cases. Every explicit resolved scope
must contain only named files at candidates, packed sources and historical snapshot.
The comparison must distinguish both FAQ identities and not interpret absence of a
statement as its opposite. Report missing evidence instead of guessing.

All 11 service requests must complete with valid citation IDs. Complete service
mean <=10 s/P95 <=20 s, first nonempty service delta P95 <=10 s, max generation
input <=12000 tokens, ingestion <=120 s. Provider generation versus first delta,
service completion versus first delta and scope/retrieval/packing timings remain
separate. N, mean, median P50 and nearest-rank P95; sequential, queue/provider wait
included, local device recorded, no HTTP/browser latency or load-capacity claim.

Retain complete measurement inventory. Final evidence coverage for answerable
cases must fully cover annotated spans; ranking uses annotated relevant child
spans at K=5 (labels incomplete beyond required evidence, precision qualified).
No-answer/no-retrieval cases are not zero-recall cases. Billed cost unavailable
unless returned; skipped provider stages are not measured zero-duration calls.
Update/delete/browser checks use the separate retained offline workflow records.

Passing supports the implemented default v1 path together with current backend,
frontend and browser checks, not general model reliability or optional experimental
configurations. User approval is still required for any merge; never merge here.
