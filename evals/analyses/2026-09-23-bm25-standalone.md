# Standalone BM25 Smoke Check

Date: 2026-09-23. This is an offline check of the standalone lexical scorer,
not an end-to-end answer evaluation. It made no provider calls and did not alter
the live library, server configuration, or previous evaluation records.

Input: the 92 stored children from the
[parent-child library snapshot](../library-runs/20260923T205040Z-parent-child/after-chunks.json).
Settings: top-k 5, k1 1.2, b 0.75. The shared word tokenizer splits identifier
punctuation, case-folds text, and preserves decimal numbers. It does not remove
stop words or perform stemming. Scores use child text only, without synthesized
heading prefixes or parent text.

| Query | Observed result |
| --- | --- |
| Original GPA question: "What academic progress requirements does the general FAQ specify?" | Rank 1 is child 0 of the general FAQ. This child does not itself contain the GPA rule, but its recorded parent contains GPA 3.0 and the 66% completion rule. None of the five returned children directly contains that rule. |
| "minimum GPA 3.0 66%" | Rank 1 is general FAQ child 1, containing both numeric requirements. |
| "DS GA 1002 waived transcripts syllabi" | Rank 1 is general FAQ child 1, containing the course waiver and required materials. |
| "ANTHROPIC_API_KEY" | Rank 1 is Anthropic-guide child 7, the environment-variable code block. |
| Original CPT comparison question | Rank 3 contains the Industry Concentration's first-year internship requirement; rank 4 contains the admissions FAQ's after-first-year CPT statement. |

All top-five matches, exact source text, IDs, offsets, scores, and the input
snapshot hash are preserved in
[2026-09-23-bm25-standalone.json](2026-09-23-bm25-standalone.json).

These results support proceeding to RRF integration, not claiming the live
failures are fixed. The original GPA query benefits only if the right parent
survives later fusion and packing. The CPT query still requires two sources to
survive the evidence budget; its known budget exclusion is not solved by a local
BM25 score. No answer generation, parent expansion, fusion, or reranking was
performed by this module during the check. The parent-content observation above
is an inspection of the stored snapshot.

This small, known set is a regression-oriented smoke check, not a held-out quality
benchmark. Explicit keyword queries differ from the original natural-language
questions and are labeled separately. The scoring module remains disconnected
from the active API/CLI retrieval path until the next implementation step.
