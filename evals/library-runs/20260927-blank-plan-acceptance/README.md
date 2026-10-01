# Explicit blanks and planner coverage: scoped functional gates pass

All six requests completed and all **24/24 requested points** were correct and
complete under single Codex review. All **21/21 factual paragraph/bullet groups**
have supporting citations. Both modes explicitly report the two Rentals cells as
blank, and the planned state comparison completes correctly. The frozen functional
gates pass; user acceptance, independent review and any merge remain separate.

Product code was fixed at `18a9922` on `v2` during this run. The same PDF, extraction,
chunks, embeddings, questions, fact annotations and runtime settings are reused
from the [previous run](../20260927-table-cell-context-acceptance/README.md).
No ingestion, reindex, retries, additional answer requests or paid judge occurred.

## Matched answer comparison

| Question / mode | Previous | Current |
| --- | --- | --- |
| Alabama values and disclaimer / single | 5/5 points | 5/5 points |
| Alabama values and disclaimer / planned | 5/5 points | 5/5 points |
| Three state totals / single | 3/3 points | 3/3 points |
| Three state totals / planned | Planner error; semantic scores unavailable, three points undelivered | 3/3 points |
| Grouped and blank cells / single | 2/4 points; incorrectly said both blanks were unestablished | 4/4 points; both cells explicitly blank |
| Grouped and blank cells / planned | 4/4 points | 4/4 points |

Correctly delivered points rise from **19/24 intended opportunities to 24/24**.
The baseline's three error-associated semantic scores remain unavailable rather
than being rewritten as zero. Completion rises from 5/6 to 6/6. No previously
correct requested point regresses. Factual-group denominators differ because the
single dense answer combines four values in one bullet, the single blank answer
combines two blanks, and the planned state answer adds a supported comparison.
The original paragraph/bullet rubric is unchanged; all group text is preserved in
[manual review](review/reviewed-cases.json). No unsupported missing-information
statement remains in the final answers.

## Source and planner checks

The [actual SDK context audit](metrics/actual-context-audit.json) verifies all six
rendered contexts, canonical excerpts, complete cell bindings and page provenance.
The planned state comparison uses 2,299 tokens; the other five contexts use 2,604,
within the unchanged 4,096-token budget. Every requested fact is supplied, including
full row/group headers, explicit blank observations and the background-check disclaimer.

The new planner prompt correctly associates comparison requirement r4 with all
three state queries in this live sample. No live request needed the new coverage
completion branch. Its behavior is separately verified by replaying the exact
previous failed model output offline: the original three queries are preserved,
one original-question query addresses r4, and the raw output/addition remain
separate in saved trace/history. The [offline record](../../check-runs/20260927-blank-plan/README.md)
retains 278 passing tests, the six-query bound, invalid-ID rejection, scope/history
integration and the same twelve packing controls. All 40 frozen dense/financial
evidence points remain covered; financial context costs reach 4,041 of 4,096 tokens.
Financial answer generation and broader corpus quality were not reevaluated.

## Remaining controller issue

One generated requirement in the grouped planned request is the conditional
instruction: "If the supplied excerpts do not establish a requested cell's contents,
state that limitation." The evidence assessor marks this R5 requirement `missing`,
yet its own gap text says all contents are established and no limitations remain.
The other 13 requirements across the three planned requests have supported statuses
consistent with supplied evidence. This inapplicable conditional instruction should
not produce a missing-evidence signal. It is a remaining status-quality issue,
recorded in the [assessment reference review](review/assessment-reference-review.json),
not a failure to retrieve the table or answer the four requested cell questions.
No supplementary query was proposed; the controller stopped with `no_eligible_query`
and the final answer correctly reported both blanks. This run therefore supports
the frozen answer gates, not a claim that every sufficiency decision is correct.

## Measurements and limits

The [complete measurement inventory](metrics/measurement.json) separates all 20
metrics for each mode, all requests and preparation. K=5 selected-child diagnostics:
fact Recall, Hit Rate, MRR and binary NDCG are 1.0; binary child Precision is 0.266667.
Final supplied-evidence coverage is 24/24. Candidate labels are limited to this
annotated development subset; these are not held-out generalization results.

| Mode | Samples | Mean first answer delta | Mean complete response |
| --- | ---: | ---: | ---: |
| Single | 3 | 2.018 s | 2.463 s |
| Planned | 3 | 8.026 s | 8.489 s |
| All | 6 | 5.022 s | 5.476 s |

The inventory includes P50/P95, individual timings, stage boundaries, sample counts
and full rankings/exclusions. Startup is excluded; provider/network waits are
included. One sample per case/mode, generative variation and the two simultaneous
changes prevent causal performance attribution. The previous failed request had
no answer delta and remains separate in comparison. At concurrency one, the
33.053-second command completed 0.182 requests/second; this is not load capacity.

All six requests completed with zero errors, timeouts and retries. There were 27
SDK calls: 15 query embeddings and 12 GPT responses (six answers, three plans,
three assessments). Resolved `gpt-4.1-2025-04-14` usage was 39,305 input tokens,
1,924 output tokens and zero reported cached input tokens. `text-embedding-3-small`
used 380 input tokens. Billing and local compute cost remain **unavailable**, not
zero. Provider usage is measured, not a billing estimate.

Review is by one Codex agent plus mechanical provenance checks, matching the
immediate baseline's reviewer setup. No independent second semantic reviewer or
human review is available. Original corpus/gold artifacts and all earlier failures
are unchanged. The [integrity record](run-integrity.json) confirms six fresh
conversations, source/history parity, unchanged baseline index and .env, and a
stopped server with a closed port and released owner lock. Source-format checks
exclude immutable raw context text whose tab delimiters encode blank table cells.

No feature acceptance, broad v2 completion or merge into `main` is implied.
