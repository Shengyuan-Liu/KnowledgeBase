# Dense table: frozen six-request live acceptance

Freeze [the questions and expected facts](frozen-cases.json) before any answer
request, at product commit `8d3403e8c16142be863f0a2e779bd9cb78d14be2` on `v2`.
Run each of the three questions once in `single` and `planned` mode: six
sequential production HTTP/SSE requests, concurrency one, alternating mode order
by question, zero provider retries, and no automatic reruns. Every request starts
a fresh conversation scoped to `background-checks.pdf`. Hold product code,
prompts, questions, budgets, and settings fixed throughout the six requests.

The source-bound [offline gold](../../check-runs/20260927-dense-table/gold.json)
was transcribed by a Codex assistant from the
[original page image](../20260927-v2-pdf-live/source-review/background-checks-1.png),
not from corrected parser output. Reviewers are Codex models, not human reviewers;
no paid judge is called. The gold covers three development rows, not the whole
table or a held-out population.

## Questions and expected points

| Case | Required points per arm |
| --- | --- |
| `dense-table` | The verbatim original question: Alabama Permit 18,870, ungrouped Handgun 23,022, ungrouped Long Gun 22,650, Totals 71,137, and the distinction between background checks and firearms sold. Five points. |
| `state-totals` | Alabama Totals 71,137; Alaska Totals 7,095; Arizona Totals 27,087, all for November 2015. Three points. No arithmetic comparison is required. |
| `grouped-and-blank-cells` | Alabama ungrouped Handgun 23,022; Pre-Pawn Handgun 14; Rentals Handgun blank; Rentals Long Gun blank. Four points. The question does not reveal these values or that the cells are blank. |

There are 12 requested points per arm and 24 point instances across six requests.
All questions are answerable from the original page. In the third question,
reporting what the page records includes identifying a printed empty cell;
it does not require inventing an unknown real-world rental count.

For each table fact, use the full header path and the original state row, source
hash, reporting month, and physical page. `Handgun` is distinct from
`Pre-Pawn > Handgun`, `Rentals > Handgun`, and other repeated leaf labels. The
annotation's table key is independent of parser table IDs and extraction offsets.
Bind evaluation labels to the new extraction using actual structure and location,
then preserve that binding before judging rankings or answers. Text anchors
alone do not establish cell relevance.

## Corpus preparation and fixed runtime

Create a fresh, isolated single-PDF evaluation library and ingest the unchanged
original through the current production PDF path. Verify the original SHA-256
`4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407`.
Retain the resulting extraction revision, complete table/cell geometry, parents,
children, index settings, document identity, and index size. Record preparation
time and embedding usage separately from the six answer requests. A fresh index
is required to exercise the repaired extraction rather than a historical stored
revision. Production data and historical run artifacts remain unchanged.

Use the verified existing configuration: GPT-4.1, `text-embedding-3-small`, K=5,
hybrid retrieval, enabled BGE reranking, and a 4,096-token evidence budget. Keep
the existing planned-search limits, including three rounds, six queries, 8,192
planner input tokens, and 16,384 answer input tokens; record resolved limits and
which request paths enforce them. Set provider timeout to 180 seconds and retries
to zero through process configuration, preserving `.env`. Record exact resolved
model names/revisions, device, cache/loading state, and all other settings.

## Independent answer and citation review

Use the existing 0 / 0.5 / 1 requested-point and factual paragraph/bullet rubric,
with the source-specific blank rules below. Score reference correctness,
completeness, supplied-evidence coverage, contextual faithfulness, relevance,
citation support, citation coverage, and abstention separately. A wrong row,
wrong parent header, or substituted value is not a correct fact merely because
the number appears in the PDF. Partial credit requires a specified supported
part with an omitted material detail; record that detail explicitly.

Inspect every actual answer and its supplied and cited source excerpts against
the original-page gold. Preserve exact factual claim groups and the supporting
source locations and header associations in the review. A supporting citation
must occur on its own factual paragraph or list item; a citation on a later
bullet does not cover an earlier bullet. A group with multiple claims needs
support for all of them, pooling only its actual cited sources. Valid IDs alone
do not establish support. Count each distinct factual group; if repeated framing
is excluded under the established rubric, retain its text and exclusion reason.

The disclaimer point requires both the background-check scope and the absence
of a one-to-one correspondence with firearms sold. Do not label the table values
as firearms sold. Additional arithmetic or explanations are not required and
must be reviewed for support if generated.

The primary reviewer and a second Codex reviewer independently inspect the
answers and supporting evidence before reconciliation. Preserve disagreements,
limitations, and their resolution; do not silently repair model output or alter
gold labels after observing results.

## Blank cells and uncertainty

A supported blank claim requires the actual Alabama row and explicit empty
cell positions at columns 16 and 17, the Rentals parent over columns 16:18, the
corresponding Handgun/Long Gun leaf headers, and physical page 1 (`page_index` 0).
Zero-length canonical cell spans can represent these empty fields. Review the
retained cell tuples, row delimiters, and associated headers together. Mere
absence of a number from a truncated excerpt does not establish a blank.

Accept "blank", "empty", or "not populated" when clearly describing those
printed cells. A blank does not state zero, no rentals, an unavailable parser
value, or any numeric rental count. Do not borrow the footer's zero or a nearby
column's value. A correct blank observation is an answer, not abstention.

If the supplied evidence cannot establish a requested cell's contents, a specific
statement of that limitation is preferable to guessing. Score such a statement
for faithfulness to the supplied context separately from reference completeness:
it does not receive full credit for reporting the original page's known blank.
Record the affected point in `missing_point_review`, indicating whether the
limitation was appropriate to the actual supplied context. If the row, empty
positions, and complete headers are supplied, claiming that nothing can be
determined is an incorrect omission rather than necessary uncertainty.

All original questions are answerable, so a full refusal counts as incorrect
abstention at the question level. Partial uncertainty is recorded per point and
does not become a full refusal. Appropriate abstention on fully unanswerable
questions is not applicable to this set. This does not prevent separately
crediting an honest statement of a real supplied-evidence limitation.

For planned mode, audit original model-selected references and application-added
table context separately. Exact quotes and retained headers improve auditability;
they do not prove the model's semantic sufficiency judgment. Check whether each
reference bundle actually retains the needed state, header group, value or empty
position, and reporting-period context. Preserve selected IDs and statuses.

## Gates, comparison, and measurements

Report scoped gates separately: six completed requests; all 24 requested points
correct and complete; all factual claim groups supported and individually cited;
correct row/group/blank distinctions; no incorrect full refusals or fabricated
counts; and response/saved-history identity for answer, sources, and retrieval
metadata. A faithful uncertainty statement caused by missing supplied evidence
does not turn the completeness gate into a pass. Passing this subset does not
establish overall v2 acceptance or authorize merging into `main`.

Only `dense-table` has a historical matched question and facts in the
[earlier review](../20260927-v2-pdf-live/reviewed-cases.json), pass `repair`.
Preserve its old results. The later product version, intervening retrieval and
citation changes, and fresh single-PDF library limit causal comparison. The two
new questions have no historical live baseline; do not invent one. Report actual
retrieval/ranking differences and per-case improvements or regressions.

Keep all attempts append-only. Save exact provider inputs/outputs, retrieved
rankings, final supplied evidence, packing exclusions, assessments, errors, SSE
events, and saved history. Follow the
[measurement policy](../../measurement-policy.md), including all 20 metrics with
measured values or explicit `not_applicable` / `unavailable` reasons. Distinguish
candidate retrieval, reranking, and final evidence coverage using the frozen
cell/fact labels; empty-cell relevance must be structural, not substring-based.

Measure first nonempty answer delta and complete HTTP stream closure separately,
including failures; report stage timings, means and percentiles, sample counts,
actual token usage, reliability, and sequential throughput. Keep preparation and
model loading separate, disclose queue/loading scope, and mark actual billing
unavailable unless supplied. Quality and performance remain separate findings.
