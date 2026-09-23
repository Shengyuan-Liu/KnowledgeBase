# Standalone RRF Replay

Date: 2026-09-23. This offline check combines newly computed BM25 ranks with
previously recorded vector candidates. It makes **zero new provider calls** and
does not change the running application's retrieval path or library.

Inputs are the 92-child snapshot and recorded vector hits from the
[parent-child library comparison](../library-runs/20260923T205040Z-parent-child/README.md).
Each route supplies up to five candidates; the fusion limit is 20 and `k=60`.
This bounds the replay to the existing candidate pools. It does not simulate a
larger vector search, a reranker, or a different evidence budget.

| Original question | Observation after fusion |
| --- | --- |
| General FAQ academic-progress requirements | General FAQ child 0, present only in BM25 at rank 1, enters the fused list at rank 4. Its stored parent contains the GPA and credit-completion requirements. The child itself does not contain those facts. The three higher fused hits are shared by both routes and do not supply that parent. |
| Admissions FAQ versus Industry Concentration internship timing | The admissions FAQ child containing "after the first year of the degree" moves from vector rank 5 to fused rank 2; its BM25 rank is 4. The Industry Concentration child is fused rank 1, so both perspectives are represented near the top of the candidate list. |
| Anthropic-compatible API setup | The invocation heading child is fused rank 4. Several other children of its invocation parent also appear. The compatibility introduction is rank 1, so fusion is not a direct measure of answer relevance. Parent deduplication remains a separate later operation. |

[2026-09-23-rrf-standalone.json](2026-09-23-rrf-standalone.json) records the questions,
route hits, separate raw scores, route ranks, RRF scores, final ranks, exact child
text/metadata, and SHA-256 hashes of both source snapshots.

These observations show how fusion can retain single-route candidates and promote
shared candidates. They do not establish that the known answer failures are fixed:

- The GPA parent still needs to survive the final evidence budget. Ranking it at
  position four alone does not ensure its inclusion.
- The CPT parent was previously excluded during packing. Moving its child earlier
  is promising, but this replay does not perform packing or generate an answer.
- Multiple selected children may share a parent; fusion intentionally retains
  their separate identities for future child-level reranking.
- These three known cases are a focused development check, not held-out evaluation.

The next step is to connect eligible BM25 and vector candidates to RRF in the
retrieval service, preserve route diagnostics through parent expansion and saved
answers, and test upload/delete/restart behavior plus the actual final evidence.
