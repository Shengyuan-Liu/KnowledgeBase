# Preserve ranked financial evidence and nearby table context

This offline component repair starts from `28ad66a` on `v2`. It addresses the
financial evidence-packing failures recorded in the
[previous live run](../../library-runs/20260927-v2-pdf-live/README.md). No provider
calls, answer generation, parser rerun or index changes were performed. The
assessor quote-selection failure and dense-table extraction omissions remain
outside this change; this record does not establish live feature acceptance.

## Behavior and regression coverage

The old `parent_then_child` packer admitted every fitting parent before trying
children of omitted parents. An irrelevant cash-flow parent therefore consumed
space ahead of the higher-ranked sales rows. The shared packer now walks selected
hits in rank order, tries a parent once, and immediately tries that whole child
if its parent cannot fit. Later siblings remain eligible in order; an admitted
parent already represents its selected children. `parent_first` retains the old
parent-only control. Nothing is truncated or fetched to fill unused capacity.

This applies to all source formats. Under a tight budget, an earlier child can
now take a slot previously occupied by a later flat hit; the existing packing
regression asserts that intentional priority change. It is not a child-first
reservation algorithm: a high-ranked parent that fits can still consume budget
needed by later answer points.

PDF evidence also includes the immediately preceding paragraph when it belongs
to the same heading path and the table's first physical page. The new
`preceding_text` supplement retains exact text, offsets and regions. The Apple
statement's `(In millions, ...)` paragraph is now supplied with a split sales row,
alongside its period headers. Existing captions/notes and text inside the excerpt
are not added again. This is structural adjacency, not a semantic certification
of units. Running page headers/footers are excluded: code review found four actual
DocLayNet table predecessors labeled `page_header` despite `kind=paragraph`.

`build_context()` still charges every citation label, metadata field, cell
coordinate, header, warning and supplement against the same **4,096-token**
budget. Canonical chunks, extraction revisions and original PDF files remain
unchanged. No reindex or database migration is needed; historical snapshots are
not repacked. The generic source viewer already supports the new supplement role.

Tests use the actual saved financial candidates through
`pack_retrieval_candidates` and SQLite, and check all six financial case/mode
pairs for values, periods, units, priority, exact canonical slices and budget.
Other tests cover sibling deduplication, the parent-only control, exact budget
boundaries, same-section/page association and saved PDF provenance/history.

## Frozen before/after evidence comparison

[Inputs](frozen-inputs.json) freeze the selected child IDs, ranks, questions and
settings from all 32 mode/question pairs in the prior repaired live pass. The
five-PDF corpus, extraction snapshot and original-page anchor annotations are
reused by hash. Retrieval, query plans, reranking, chunking, K=5 and the budget are
fixed; only evidence attachment and packing change. This isolates packing behavior
without rerunning stochastic model calls or claiming a retrieval improvement.

[Before](before.json) reproduces the recorded source positions and token counts.
[After](after-2.json) retains the new exact contexts and diagnostics.
[Comparison](comparison-2.json) contains every case, changes, timings and the
complete 20-metric inventory. The earlier `after.json`/`comparison.json` are
preserved: a subsequent review excluded unrelated running headers, with no change
to the aggregate anchor score.

| Financial pair | Context tokens before -> after | Evidence outcome |
| --- | ---: | --- |
| Sales, single | 2653 -> 2712 | Sales values and periods recovered; same-page units included |
| Sales, planned | 3843 -> 2712 | Sales retained; units now attached to that statement |
| Income, single | 3843 -> 2712 | Equivalent supported values/units now come from annotated page 1 |
| Income, planned | 3843 -> 2712 | Same evidence change; live assessor behavior remains untested |
| Period comparison, single | 3994 -> 3884 | Correct sales row and header periods recovered |
| Period comparison, planned | 2788 -> 4019 | Correct sales row and header periods recovered |

Codex source review confirms all six repaired contexts contain the requested
values, the quarter/year column mapping, and the exact units paragraph. The
original-page figures are unchanged: sales 94,930 / 391,035; income 14,736 / 93,736,
for three/twelve months ended September 28, 2024, in millions. These are facts in
the supplied context, not newly generated answers or observed citation quality.

Over the 28 fact-bearing pairs (14 questions x two modes, 72 fact instances),
macro **literal source-anchor coverage rises from 69.29% to 88.33%**. Six pairs
improve and none regress under those annotations. The four no-gold pairs are
excluded, not scored as zero. Labels are incomplete: the income cases already had
semantically equivalent page-4 evidence before this repair, so their page-1 anchor
gain is **not** an answer-quality gain. Likewise, `Yaoliang Yu` is semantically
present but its joined extraction misses the literal anchor; four Alabama values
remain absent. Do not read the aggregate as an accuracy percentage.

Candidate-stage diagnostics stay fixed by construction: Recall@5 .7583,
Precision@5 .3500, Hit Rate@5 .9286, MRR@5 .8333, NDCG@5 .7305. Recall requires all
anchors of a fact; child relevance means intersecting any annotated anchor.
Precision divides by five, even with fewer hits; binary NDCG uses log2 discounts.
Per-case values and the incomplete-label warning are retained in the comparison.

Quality of newly generated answers, faithfulness, citation support/coverage,
abstention, first-answer-delta/complete-response latency, provider usage/cost,
ingestion and production load are **not applicable** to this offline replay.
Local evidence attachment/packing timings (32 cases each, linear percentiles):

| Local stage | Mean | P50 | P95 |
| --- | ---: | ---: | ---: |
| Before | 4.99 ms | 1.64 ms | 11.38 ms |
| After | 5.26 ms | 1.65 ms | 12.80 ms |

These include first-use local tokenizer setup, exclude parsing/models/providers/
network/queue waits, and are not user-response latency or a speedup claim. Average
context size changes from 2263.34 to 2197.31 tokens across all 32 pairs. Device and
Python source hashes are recorded per command; local computation has no measured
monetary cost.

## Verification and retained attempts

- [Packing and retrieval checks](packing-tests-1.log): 39 passed.
- [Table context checks](units-tests-2.log): 15 passed; initial 14-test pass retained.
- [Full backend checks](backend-tests-1.log): **736 passed, 1 skipped**, 26.50 seconds.
  Existing Starlette and OCR-option deprecation warnings remain; no new warning.
- Final record review checks source/code/fixture identity, baseline parity,
  canonical spans, budget limits, documentation links and formatting.

The first replay attempt failed because Pydantic's base-typed nested serialization
omitted structural fields. The harness now reloads the unchanged typed child by
its frozen ID from the hashed index snapshot; the failure is retained in
`before-record.json/log`. Product source was unchanged until the successful
baseline had been captured. All comparison attempts and intermediate results are
append-only. Generic offline command inventories apply to the command invocation;
`comparison-2.json` supplies the measured component metrics. A wrapper's zero
regex test counts for a non-pytest helper are not a count of executed assertions;
its exit status and retained output establish command success.

Independent read-only code review found and verified the running-header exclusion.
The review is by Codex agents, not an independent human acceptance reviewer.
Remaining work: replace fragile free-form assessor quote selection, then run a
separate live acceptance pass when the relevant repairs are complete. Dense-table
fidelity remains a separate unresolved limitation. No merge into `main` is implied.
