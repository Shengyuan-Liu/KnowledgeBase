# Assessment passage selection: offline contract verification

The sufficiency assessor now selects local passage IDs instead of writing its own
quotes. The application resolves selected IDs to exact canonical text, offsets,
file identity and PDF physical pages. This removes free-form quote transcription
from this response contract. Semantic selection and live model reliability remain
unmeasured: this run made no provider calls and generated no answers.

The historical `apple-income-planned` model response joined separated table rows
with an inserted ellipsis. It still fails its original strict source validator.
That request, response and error are retained in
[historical-invalid-quote.json](historical-invalid-quote.json) and
[before.json](before.json). Nothing in this report reclassifies that failure as a
successful model response.

## Frozen comparison

- Baseline production source: commit `a96d460`; retained copies are
  [baseline-sufficiency.py](baseline-sufficiency.py),
  [baseline-dependencies.py](baseline-dependencies.py) and
  [baseline-hops.py](baseline-hops.py).
- Both versions use the same 32 final packed contexts from the
  [preceding financial-packing repair](../20260927-pdf-evidence-packing/README.md),
  covering 16 questions in single/planned retrieval modes. The corpus, candidate
  order, packing, questions and original-page anchor labels are unchanged.
  [frozen-manifest.json](frozen-manifest.json) records immutable input hashes and
  the historical assessor control fields.
- The baseline model payload includes the answer context and excerpt metadata.
  The new payload retains that context and its table metadata, limitations and
  source identities, adding `[p1]`-style markers to exact nonblank source lines.
  The complete local passage catalog is saved for provenance but is not duplicated
  in the model request. Output references contain only `evidence_id`.
- Requirements, executed searches, pending dependencies and remaining budgets
  come from the last historical planned assessment for each question. Reusing
  those fields with single-mode contexts is an offline input-size diagnostic, not
  a claim that the single mode called this assessor in the live run.
- The prior financial-packing repair changed the historical failing context.
  Therefore the raw historical failure is replayed separately against its own
  original sources. The component comparison uses current packing on both sides.

[replay.py](replay.py) records exact serialized model inputs, output schemas,
catalogs, token counts and local construction durations in [before.json](before.json)
and [after.json](after.json). Production file hashes identify the after version.
Saved base-model chunk dictionaries omit structured heading fields; the replay
restores their typed metadata from the immutable original index before rendering.

## Evidence and contract results

All 32 constructed requests fit the unchanged 8,192-token assessor cap. Removing
only the injected passage markers reproduces each original answer context
byte-for-byte. Every selectable passage is an exact canonical substring contained
in a previously supplied source body or PDF supplement, with physical page indices.
The answer model's context and 4,096-token evidence budget remain unchanged.

The manual income fixture selects four separate passages:

| ID in this assessment | Source meaning | Canonical offsets | Physical PDF page |
| --- | --- | --- | --- |
| `p1` | Three-month and twelve-month headings | `170:209` | 1 |
| `p2` | Column dates | `209:285` | 1 |
| `p20` | Net income values | `1014:1061` | 1 |
| `p28` | Unit statement | `73:168` | 1 |

These choices were authored by Codex as a deterministic contract fixture. The
application reconstructs the same exact quotes and offsets as a manually correct
baseline quote response, preserving newlines. Both manual fixtures validate;
neither is a new model result or a measurement of semantic correctness. Saved
`page_indices` are zero-based. IDs are local to one assessment and may identify
different passages in another round.

Literal source-anchor coverage remains **0.883333** across 28 fact-bearing pairs
and 72 fact instances, with no case regressions. Four no-gold pairs are excluded.
The before measurement uses supplied excerpt spans; the after measurement uses
the union of selectable passage spans. This is evidence coverage, not answer
accuracy. Existing joined-text anchor mismatches and dense-table missing values
remain unchanged.

Frozen candidate diagnostics at K=5 also remain unchanged: Recall 0.758333,
Precision 0.350000, Hit Rate 0.928571, MRR 0.833333 and NDCG 0.730516. These are
recomputed from the same selected children, not retrieval improvements. The
original-page labels are incomplete; metric definitions and per-case scores are
retained in [comparison.json](comparison.json).

## Input size and local performance

| Metric, n=32 per version | Before | After |
| --- | ---: | ---: |
| Mean assessor input tokens | 4,044.56 | 3,759.97 |
| P50 input tokens | 4,028 | 3,818 |
| P95 input tokens | 6,173.45 | 5,718.25 |
| Maximum input tokens | 6,480 | 5,835 |
| Inputs over 8,192 | 0 | 0 |
| Mean local construction time | 1.016 ms | 0.922 ms |
| P50 local construction time | 0.944 ms | 0.954 ms |
| P95 local construction time | 1.648 ms | 1.300 ms |

Token counts use the production `cl100k_base` serialized messages-plus-schema
counter, including instructions and output schema. They are local budget estimates,
not provider billing usage. Per-case input deltas range from -927 to -63 tokens.
The input representation changed; this is not an isolated tokenizer comparison.

Timing includes passage/catalog construction, schema/request serialization and
local input-token counting, with the tokenizer prewarmed. It excludes snapshot
restoration, payload copying, model loading, network calls and queue waiting.
Both versions run sequentially on the developer machine; sample distributions use
linear percentiles. A single local pass does not establish production latency,
throughput or a speedup. Device and raw durations are retained in the records.

The recorded design exploration in
[catalog-layout-exploration.json](catalog-layout-exploration.json) measured a
duplicate per-line text catalog beside the full context. Canonical IDs exceeded
the cap in 9/32 inputs and short IDs in 5/32. The implemented inline annotation
avoids duplicating source text. The exploratory cap overages remain visible.

## Checks and retained attempts

Each command has an append-only JSON record and raw log. The complete 20-metric
component inventory is in [comparison.json](comparison.json). Test command
records separately mark live quality, provider cost and production performance
as not applicable. Counts in the generic wrapper are parsed pytest summaries;
non-pytest scripts use assertions and have zero parsed test counts.

| Check | Result | Record |
| --- | --- | --- |
| Catalog-layout exploration | Completed; duplicate-text approaches exceed the cap as above | [record](catalog-layout-exploration-record.json) |
| Baseline input replay | 32 inputs; historical invalid quote rejected | [record](before-record.json) |
| New input replay | 32 inputs; exact spans/pages, unchanged context and manual ID selections verified | [record](after-record.json) |
| Frozen comparison | Same evidence coverage and rankings; all 20 metrics recorded | [record](comparison-record.json) |
| Sufficiency scoped tests | 50 passed | [record](sufficiency-tests-1.json) |
| Initial PDF assessment tests | 26 passed, 3 failed | [record](pdf-assessment-tests-1.json) |
| Corrected PDF assessment tests | 29 passed | [record](pdf-assessment-tests-2.json) |
| Initial backend suite | 742 passed, 3 failed, 1 skipped | [record](backend-tests-1.json) |
| Final backend suite | 745 passed, 1 skipped; two existing dependency deprecation warnings | [record](backend-tests-2.json) |
| Targeted offline browser checks | 4 passed | [record](browser-tests-1.json) |

The three failed assertions came from the newly written test fixtures: restoring
chunks as their base type dropped heading metadata, and a financial selector
picked a combined period header from a later reconciliation page while the
desired first-page periods were separate supplements. The fixtures were corrected
to restore typed metadata and select the intended first-page passages. Initial
failures remain in their original logs and records.

The final backend run reports 26.68 seconds in pytest and 29.25 seconds for the
captured invocation. The two warnings concern Starlette's `BlockingPortal` alias
and Docling's `force_full_page_ocr`; they were already present before this change.
The four browser checks cover saved planned assessments at desktop/mobile widths,
cancellation during assessment, and planned PDF page navigation, reload and
retained evidence after deletion. Their provider interactions are mocked.

Codex visually inspected the
[desktop screenshot](browser-1/planning-planned-search-and-saved-evidence-at-1440px/planned-1440.png)
and [mobile screenshot](browser-1/planning-planned-search-and-saved-evidence-at-390px/planned-390.png):
the resolved exact quote and file name remain readable, and internal passage
markers do not appear in the displayed quote. This is UI review, not independent
human assessment of semantic support. The temporary browser test server was
stopped after verification.

## Remaining acceptance limits

No live ID-selection response, semantic sufficiency score, answer quality,
abstention rate, first-answer-delta latency or complete-answer latency is measured
here. Source-valid IDs alone do not show semantic support. A model can still choose
irrelevant passages or misunderstand table relationships, and unseen documents
can still exceed the unchanged planner budget. The original dense-table extraction
gaps also remain. Live acceptance should exercise the complete repaired feature
when the user elects to run it; passing these offline checks does not authorize a
merge into `main`.
