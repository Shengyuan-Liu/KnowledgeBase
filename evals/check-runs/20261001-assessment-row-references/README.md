# Assessment table references and comparison citations

Table readings now display the current passage IDs beside their row coordinates.
The six frozen contexts retain all source text and gain correct explicit markers
on **75/75 table readings**, up from zero. Answer instructions now explicitly
require citations for comparisons and computed conclusions. These are offline
rendering and prompt-delivery results, not proof of improved model behavior.

## Observed failure and focused change

The [preceding live run](../../library-runs/20260929-pdf-heading-acceptance/README.md)
supplied and answered all 16 reference points but passed only 5/6 case gates.
Its cash-flow comparison omitted an inline citation. The assessor separately
selected `p15` (inventory) for operating cash and `p31` (debt issuance) for financing
cash. The correct operating/financing readings had table coordinates `Row 15:16`
and `Row 31:32`, while their actual passage IDs were `p19` and `p35`. This exact
numerical correspondence suggests coordinate/ID confusion; it does not establish
the model's internal cause. An extra irrelevant inventory reference also appeared
in the securities assessment.

`assessment_context` now uses canonical offsets embedded by `_table_reading` to
find overlapping catalog passages within the same file and print their markers
beside each table reading. It does not calculate IDs from row coordinates. A
reading may reference several source lines. The general context renderer accepts
an optional table-reading renderer; ordinary answer context remains byte-identical.
The assessor instructions distinguish these number systems and require checking
the row label, measure, column group and period before selecting a passage. The
assessment prompt version is `evidence-sufficiency-v6`.

The shared synchronous/streaming answer instructions explicitly require source
citations for arithmetic results, comparisons and statements that a factual
condition is met. An example uses two distinct sources to show that cited operands
in earlier bullets do not cover a later conclusion. This follows the use of
explicit instructions and examples described in the official
[GPT-4.1 prompting guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-4.1).
The model and provider settings are unchanged.

No model decision is rewritten, no semantic row-selection heuristic is added,
and no citation is inserted after generation. Valid passage IDs still establish
provenance only. The previous incorrect selections and uncited answer remain
unchanged in the historical artifacts. This change needs no PDF reindex.

## Frozen before/after comparison

[Input hashes](frozen-inputs.json) retain baseline `e02c8c3`, the same six questions,
five-PDF snapshot, source-span annotations and full answer traces. Both arms reuse
the exact final selected evidence and recorded assessment; retrieval, planning,
assessment and generation are not rerun. Before rendering exactly reproduces the
recorded assessor input messages and local token counts for all six cases.
[Before](before.json) and [after](after.json) retain full contexts, catalogs and
generation messages. [Comparison](comparison.json) includes all 20 policy metrics.

| Case | Table readings with explicit IDs before -> after | Assessor local input tokens before -> after |
| --- | --- | --- |
| Paper split | No table readings | 5487 -> 5572 |
| Paper delivery | No table readings | 5209 -> 5294 |
| Lecture bag of words | No table readings | 2895 -> 2980 |
| Missing lecture date | No table readings | 2380 -> 2465 |
| Current/non-current securities | 0/40 -> 40/40 | 6895 -> 7100 |
| Conditional cash flow | 0/35 -> 35/35 | 5959 -> 6149 |

All assessment inputs, including their schema, remain below 8192 tokens. The
generation instruction adds 111 local input tokens per rendered case; all remain
below the unchanged 16384-token answer limit. The all-missing date request would
still short-circuit without generation; its message count here is a rendering
diagnostic. These are local `cl100k_base` counts, not provider usage or billing.

All catalog entries, canonical text, offsets, page references, table values,
answer user messages and answer evidence contexts remain unchanged. Frozen
supplied fact-anchor coverage stays **16/16 -> 16/16**; there is no new quality or
retrieval-ranking result. The table markers are navigation metadata rather than
new evidence. The 4096-token answer-context limit is unchanged; the separate
assessor input limit still accounts for its annotations and schema.

## Verification, failures and limits

- [Scoped regression](scoped-1.json): **161 passed**, one existing Starlette
  `BlockingPortal` deprecation warning. Covers the six real frozen contexts,
  actual confusing cash-flow coordinates, synchronous/streaming prompt delivery,
  sufficiency, generation, citations, PDF evidence/table packing, planned and
  dependent retrieval, and PDF integration.
- [Initial focused attempt](focused-1.json): **32 passed, 1 failed**. The old
  income test expected pre-compaction JSON whitespace in a legacy table snapshot.
  The [baseline probe](baseline-probe.json) confirms identical baseline/current
  user messages and that this historical comparison already failed at `e02c8c3`.
  The test now normalizes only that table JSON whitespace; all source content
  still compares exactly. The original test is retained under `attempts/` and
  raw historical evidence is unchanged.
- Both [before capture](replay-before.json) and [after capture](replay-after.json)
  pass their catalog, source-preservation and input-budget assertions. The new
  comparison test deliberately returns the original uncited model output through
  both mocked paths, verifying that no passing answer is fabricated by repair.

No paid calls, provider usage, fresh semantic assessments, ingestion, browser or
load checks occur. Offline test durations are not production latency. The report
marks these metrics not applicable with reasons. The latest live quality evidence
remains the preceding 5/6 result. Next, run one matched acceptance on the unchanged
six-case corpus and inspect both assessor-selected rows and every answer citation.
This change and its passing tests do not authorize a merge.
