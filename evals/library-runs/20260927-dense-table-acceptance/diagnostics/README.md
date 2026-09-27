# Offline diagnosis of the frozen dense-table acceptance failure

The recovered target cells reached the index and ranked candidates, but the table evidence could not fit the configured source-context budget. A separate filename-clause parsing error stopped both grouped/blank-cell requests before any provider call. The single-search state comparison also produced unsupported values despite receiving only notes. These are distinct failures; a citation number passing syntax validation does not establish support.

Reviewer: Codex assistant `/root/citation_design_review`, not a human reviewer. Production remained at `8d3403e8c16142be863f0a2e779bd9cb78d14be2`. No product edits, parser execution, server requests, provider calls, or proposed-fix trial were performed. Local probes used the existing production functions and frozen run artifacts. Their command records are [diagnostics-1](../diagnostics-1.json) and [diagnostics-2](../diagnostics-2.json); raw output remains in the corresponding logs.

## Evidence packing

The frozen first child contains the complete original-annotated Alabama, Alaska, and Arizona rows, together with the report title, date, and column headers. The [retained row/cell audit](three-state-rows.json) records their text, positions, and physical page; this is not an accuracy claim for other table rows.

Counts below use `cl100k_base` on the actual `build_context` output. They measure source serialization, not provider billing or the whole answer prompt.

| Region | Body tokens | Full source-context tokens | Cell tuples | Fits an empty 4,096-token budget |
| --- | ---: | ---: | ---: | --- |
| Child 0, offsets 0:942 | 501 | 4,673 | 221 | No |
| Parent 0, offsets 0:2339 | 1,495 | 14,631 | 671 | No |
| Notes child 7, offsets 4907:5738 | 154 | 305 | 0 | Yes |

For child 0, source identity plus body costs 534 tokens, page/offset metadata adds 17, the table-coordinate section adds 4,024, and extraction warnings add 98, for exactly 4,673. There are 46 included header tuples and no separately located header supplements because the headers already lie inside this child. All seven children intersecting the table exceed 4,096 tokens even in isolation: their serialized sizes range from 4,104 to 6,867. [Full inventory](context-inventory.json), [child 0 context](child-0-context.txt), [child 0 evidence](child-0-evidence.json), and [parent context](parent-of-child-0-context.txt) preserve the measurements and exact serialization.

The [actual retrieval snapshots](actual-retrieval.json) show child 0 among the selected candidates for both Q1 and Q2 arms, then excluded by `context_budget`. It ranks second for Q1 single, and first in the final candidate order for Q1 planned and both Q2 arms. Thus the observed failure occurs after candidate selection; it is not caused by the absence of these target values from the new extraction. `pack_evidence` correctly charges the full serialized context and accepts only complete parents or child fallbacks. Its exclusion record reports body tokens (501 for this child), which understates the actual size that caused rejection.

Smallest next-fix direction: make the supplied table representation budget-efficient while retaining exact cells, blank positions, header spans, and citation locations. Start with lossless compact serialization; if necessary, make table slices respect their full rendered evidence cost. Record full trial token counts in exclusions so the cause is visible. This diagnosis does not prove any proposed representation fits or improves model answers; no alternate representation was executed.

## Quoted filename followed by a date modifier

The frozen Q3 begins `In "background-checks.pdf" for November 2015, ...`. The prefix regex in `document_references` accepts `In`; its delimiter scan stops at the comma outside quotes, rather than the closing filename quote. The final quote/space trim therefore returns `background-checks.pdf" for November 2015`. The quoted name and the temporal modifier become one reference. The ready file exists and its ID is explicitly selected, but reference resolution still requires this malformed reference to match the narrowed catalog.

The [first scope replay](scope-reproduction.json) exactly reproduces the single-search error. Its planned comparison is intentionally recorded as unequal: the initial scope error is not the planned request's final message. Inspection of `prepare_planning` shows it discards that first scope result and propagates an empty allowed-file list. `retrieve_plan` then resolves again against an empty catalog while the original explicit file ID remains selected; the existing missing-ID branch returns the generic message that the selected document is missing or not ready. The [second scope replay](scope-plan-followup.json) exactly matches that final planned scope. Both live requests made zero SDK calls. The generic message does not mean the uploaded file was actually missing.

Smallest next-fix direction: bound an explicitly quoted filename by its closing quote while preserving the following temporal constraint as question text, and retain the initial scope failure through the planned path. Preserve the selected-file restriction and existing ambiguity checks; do not introduce global fallback or treat a date modifier as a document identity.

## Actual generation inputs and unsupported totals

The three final model streams (Q1 single, Q1 planned, and Q2 single) received byte-identical 305-token source contexts: one notes/disclaimer excerpt at offsets 4907:5738, with no table tuples, supplements, or state names. Their [input audit](generation-input-audit.json) links SDK call IDs and JSONL line numbers, and each exact input/context is saved beside it. Q2 planned had no final model stream and returned the application's insufficient-evidence message.

Q2 single nevertheless answered Alabama **29,801**, Alaska **5,733**, and Arizona **32,667**, each citing `[1]`. None of those three values occurs anywhere in that generation request's messages. The correct original-page totals, **71,137**, **7,095**, and **27,087**, are also absent from its supplied input. Source `[1]` contains explanatory notes, not the requested state totals. This establishes unsupported generation and false citation support; it does not establish how the model selected those wrong numbers. Existing instructions already require supported answers and explicit limitations, so a prompt-only change cannot be presumed sufficient.

Future acceptance must separately verify that table evidence actually reaches generation, that the natural Q3 filename syntax resolves, and that the model abstains when the relevant table facts are absent. No live request was repeated and no scores or frozen artifacts were rewritten during this diagnosis.
