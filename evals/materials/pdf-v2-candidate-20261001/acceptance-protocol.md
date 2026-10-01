# First-use new-PDF functional protocol

Freeze version 1 before product ingestion, planning, generation or inspection of
results. Target the current `v2` product at `7b93c61` (runtime implementation
`46d5931`). Hash the final product/configuration and this package immediately
before execution; disclose any drift. Do not change prompts/settings after opening
answers, repair responses, silently retry, drop failed questions or select a best
sample. Failed infrastructure attempts are retained separately.

## Inputs and bounded execution

Use the exact four original PDFs in [manifest.json](manifest.json), all 90
physical pages. Create a new isolated data directory; do not modify the user's
library or the prior evaluation indexes. Ingest each original once and record
upload-to-ready time, extraction/revision metadata, warnings, chunks, parents,
source offsets, vectors/settings and storage size. Do not insert the reference
page text, annotations, expected targets or gold queries into the product index.

Before answer calls, map [references](references.json) onto the actual extraction.
Preserve missing/ambiguous source mappings as extraction failures. They do not
authorize narrowing the question, changing expected facts or dropping a case.
Freeze the mapping before viewing answers; retain model-input contexts exactly.

Execute the six [questions](questions.json) once each in their recorded order,
fresh conversation per question, planned retrieval, explicit allowed file IDs,
concurrency one, no warmup and zero SDK retries. The full and restricted hop
questions are byte-identical; only the file boundary changes. Do not add the
bridge target to their request or override the generated plan. Let real planning,
binding, sufficiency and bounded supplementary retrieval run normally.

Match the preceding acceptance settings: GPT-4.1, text-embedding-3-small,
BGE reranker revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` on MPS,
4096-token evidence cap, 8192-token assessment input cap, 16384-token generation
input cap and existing controller bounds. Retain actual resolved model IDs and
settings; do not silently substitute models. Provider/client timeouts are 180/240
seconds while tighter production controller limits remain effective. Separate
startup/model loading, ingestion, answer calls and later browser/history checks.
No paid judge or answer reruns are part of this six-request protocol.

## Answer review and fixed gates

Codex is the reviewer, not a human. Review every expected point and every emitted
factual claim against original physical pages and exact final supplied context.
The annotations specify 12 unique positive facts and 13 case-fact instances:
four fully answerable requests, one partially answerable request and one fully
unanswerable request. Missing and wrong positive points score zero; count partial
completion separately from correctness. Equivalent wording and exact unit
conversion are acceptable, but values must retain period, measure and accounting
basis. A number appearing elsewhere on the page is not semantic support.

For each case, require completion, correct and explicit required facts, appropriate
gap disclosure, relevance, faithful substantive claims, supporting inline citations
for all factual claims, correct physical-page metadata, and matching saved
answer/source/trace. A fully claim-free refusal has no citation denominator.
Optional statements in a refusal still require support and citations. Report
correctness/completeness over 13 positive instances; report faithfulness and
citations over the actual emitted claim inventory, not a fixed guessed count.

For the partial case, the bridge remains answerable and must not be withheld.
The two downstream facts are unavailable in scope; supplying remembered DPR
training details fails even if they match the other paper. For the fully
unanswerable case, the future revenue outlook is a distractor, not actual results.
If mentioned, it must be explicitly identified as a forecast with a supporting
citation. Record appropriate full abstention (denominator 1), appropriate gap
handling (2 gaps in 1 partial case), incorrect full/partial abstention on four
fully answerable cases, and omission of the supported partial-case bridge separately.

Scoped answer acceptance requires all six cases to pass. Report any failure
without weakening the rubric. A pass is not full v2 release acceptance.

## Dependency execution review

Score the full hop separately, with one eligible chain:

1. Initial retrieval finds RAG's initialization relationship.
2. A later binding resolves the retriever name from a literal quote in retained
   prerequisite evidence. Inspect semantic relationship, file, source offsets and
   timing, not merely a valid ID or matching string.
3. The bound target is used in a downstream query after the prerequisite round.
4. That query retrieves the retriever paper's negative-training recipe. Final
   supplied evidence and answer must retain support for both the bridge and details.

A correct answer from prior knowledge, independent searches or first-round
incidental retrieval can pass answer quality but leaves dependent execution
unproven. Do not force a plan or manufacture a binding to obtain a pass. Record
such a result as `not_exercised`, so it cannot satisfy the dependency gate.
If an attempted chain selects the wrong entity/relation, record a semantic failure.

For the restricted twin, inspect every round and final evidence for scope
integrity. Correctly withheld downstream facts are expected, even if the bridge
can be resolved. No query/reference may expand to the excluded paper. This is a
paired scope diagnostic, not a second independent positive chain.

## Measurements and interpretation

Retain every metric required by [measurement policy](../../measurement-policy.md):
measured values, or explicit unavailable/not-applicable reasons. Candidate
vector/BM25/fusion, reranking, final selected children and packed evidence are
separate stages. For labeled child rankings use K=5, binary full-anchor relevance,
log2 discounts, reciprocal rank truncated at five and Precision denominator five.
Enumerate relevant children only inside each case's file scope. Disclose that
literal annotations do not exhaustively label semantic equivalents; accept valid
alternative evidence in semantic review. Never score the no-gold case as zero
recall. Report per-case scores and macro means over the five cases with positive
in-scope references, including the partial case with only its available bridge.

Final coverage is case-fact coverage of actual supplied text with proper table
semantics (13 positive instances); bridge coverage remains separately visible.
Measure answer correctness, completeness, faithfulness, relevance, citation
support/coverage and the separate abstention populations above. Review final
assessor selections against the same facts/gaps, including extra irrelevant rows;
application-attached headers are not model-selected references.

Measure first nonempty answer delta and complete HTTP/SSE latency separately.
Report count, mean, P50 and P95 using linear interpolation, with all request
failures visible and no zero substitution. Retain stage timings, token usage and
cache counts, actual SDK calls/errors/timeouts/retries, concurrency and throughput.
Network/queue time is included in observed response timing; separately unavailable
timers remain unavailable. Billed currency is unavailable unless returned; token
counts are not a bill. Sequential throughput is not load capacity.

This new population is not a matched before/after comparison with the earlier six
questions; do not claim a quality gain from cross-dataset score differences. No
RAG component changes in this protocol, so no component replacement comparison
is implied. A-D ablations, general accuracy thresholds and independent human
review remain broader release work. Latency is diagnostic; this preparation does
not invent a production SLA. After opening first-use results, relabel the set as
development material before any tuning/replay.

Run [browser checks](browser-protocol.md) on persisted results without generating
extra answers. Keep raw results/reviews append-only in a new run directory, link
a report from v2 documentation, and let the user decide feature acceptance/merge.
