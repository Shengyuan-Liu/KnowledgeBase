# Bounded PDF heading/body parent context

The observed lecture miss is repaired at PDF ingestion: an isolated heading parent
can share context with its adjacent body on the same physical page, within the
existing parent token limit. The matched offline replay supplies **16/16 reference
points**, up from **14/16**, with no lost reference facts across six frozen cases.
This is evidence recovery, not a new live answer-quality or retrieval-ranking score.

## Change and boundaries

The previous [full-chain run](../../library-runs/20260929-new-pdf-chain/README.md)
correctly indexed both count bullets on lecture page 62 but supplied only its
title. The following `Learning phase` heading and body lived in another parent.
That original failure and its incorrect partial refusal remain unchanged.

`join_heading_parents` in `knowledgebase/rag/pdf_chunking.py` operates on existing
structural chunks. It joins a heading-only parent with the next body parent if
both map entirely to the same physical page and their exact combined source slice
fits the original parent budget. Running headers/footers alone are not body
content. It preserves source geometry and child text/IDs/offsets/heading paths,
renumbers parents and updates child-to-parent links. It does not infer a new
heading hierarchy, expand retrieval windows, or insert explanatory text.

`services/files.py` applies this only during PDF ingestion and records
`pdf_parent_context: adjacent-heading-body-v1` with indexing settings. Existing
PDF libraries are not silently rewritten: reindex/re-upload affected PDFs to
activate the parent associations. Previous answers and extraction revisions
remain intact. The public upload path recomputes embeddings on re-upload even
though these child texts remain unchanged under the same extraction/settings.

The real cross-page `Overfitting` title on page 48 remains separate from the
page-49 body. The background-checks `NOTES:` heading does not absorb a section
containing only another heading and a footer. A 64-token parent budget keeps the
observed title/count pair separate when the combined slice cannot fit. Ordinary
TXT/Markdown chunking and the retrieval-time table-context logic are unchanged.

## Frozen comparison

[Input hashes](frozen-inputs.json) freeze the six original questions, source
extraction, 16 fact labels and complete answer traces from baseline `83f9de1`.
Both arms use the original selected child IDs, query plans, rankings, extraction
bytes and 4096-token final evidence cap. Rebuild parent records only in temporary
in-memory SQLite databases; never run a provider, vector search or reranker.
All six baseline serialized contexts exactly reproduce the live records.

| Case | Evidence points before -> after | Context tokens before -> after |
| --- | --- | --- |
| Paper split | 2/2 -> 2/2 | 3616 -> 3616 |
| Paper delivery | 3/3 -> 3/3 | 3281 -> 3281 |
| Lecture bag of words and counts | 1/3 -> 3/3 | 950 -> 1007 |
| Missing lecture date | No positive gold facts | 602 -> 641 |
| Current/non-current securities | 3/3 -> 3/3 | 4062 -> 4038 |
| Conditional cash flow | 5/5 -> 5/5 | 3359 -> 3346 |

Coverage requires every frozen fact anchor inside the actual supplied text and
canonical source ranges. The two recovered count bullets retain physical page
62. The missing-date context can change but this replay generates no new refusal.
The unchanged five-case selected-child metrics at K=5 are Recall 0.650,
Precision 0.200, Hit Rate 1.000, MRR 1.000 and NDCG 0.7233. These are limited
full-anchor labels, not exhaustive semantic relevance. Candidate rankings are
frozen, so no retrieval gain is claimed.

Parent counts change from 100 to 89 for the lecture, 8 to 4 for Apple, and 21 to
20 for the technical report; paper and background-check counts remain 22 and 3.
All 621 child records preserve their content/IDs/offsets/headings across the five
snapshot documents. Parent IDs and links can change even for an unmerged parent
because indices are renumbered. This is recorded rather than presented as a
lecture-specific hard-coded exception.

[Raw replay](replay-results.json) retains both contexts, source spans, provenance,
budget exclusions, timings and per-case improvements/regressions. The authoritative
[20-metric inventory](measurement.json) explicitly marks live answers, streaming
latency, paid usage/cost, ingestion lifecycle and load metrics as not applicable.
Local packing durations include parent loading and provenance attachment after
tokenizer initialization; they exclude parsing, embedding, model loading, network
and queue waiting. A single sample per case/arm does not establish a speed gain.

## Verification and remaining work

- [Scoped regression](scoped-1.json): **177 passed**, with one existing Starlette
  `BlockingPortal` deprecation warning. Includes PDF upload/storage/history,
  parent/child contracts, packing/table context, planning/dependency retrieval and
  file lifecycle; no real providers.
- [Focused tests](focused-2.json): **9 passed**, including the real page-62
  title-to-count expansion and ingestion persistence/unchanged embedding inputs.
- [First focused attempt](focused-1.json): **8 passed, 1 failed** because the test
  omitted required packing options from its diagnostics fixture. The corrected
  fixture and [original test source](attempts/heading-context-tests-1.py) are retained;
  no production fallback was added.
- [Replay command](replay-1.json): 12/12 local packing calls complete, all six
  baseline contexts match, exact text/provenance and budgets pass.
- Final integrity and documentation review are in `review-1.json` / `review-1.log`.
  The normalized metric inventory corrects only the relative artifact paths of
  the five frozen ranking metrics; the original replay values remain unchanged.

The live 5/6 case result is still the latest answer-quality evidence. A complete
acceptance run must reindex the affected PDFs in an isolated library and rerun
these same frozen questions and annotations. Changed context may alter early
assessment, supplementary queries and later rankings; replaying old final-round
selections cannot establish that behavior. No merge is authorized by these checks.
