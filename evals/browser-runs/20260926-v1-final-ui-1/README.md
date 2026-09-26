# Final default v1 browser acceptance

**Passed: one real-provider Chromium workflow, three completed answers, one
intentional cancellation, two uploads and two deletions.** Product code is the
accepted merge `483a156`; harness and plan were frozen in `360a982` before calls.
No product code changed. This run closes the post-merge UI workflow check, not
independent quality validation. No test retry, SDK retry, judge or paid rerun.

## Frozen scope and configuration

[PLAN.md](PLAN.md) specifies the two exact synthetic fixtures and expected answers.
[run.json](run.json) retains command, settings, code/fixture hashes, host and
power assertions, timing and original metric inventory. A new isolated data
directory was used; the ordinary `.env` and library were not changed. Default
parent-child/hybrid retrieval, top-K 5, 4096-token evidence, GPT-4.1 and
text-embedding-3-small; reranking off, omitted reasoning, 60-second provider timeout.
One worker, headless desktop Chromium, temporary `caffeinate -i -s`.

The Playwright test passed in 15.8 s; its reported runner duration was 19.0 s.
Both wrapper wall and active durations are retained in run.json. Startup is
included in wrapper duration but excluded from per-question UI latency. This was
not a throughput workload; model revisions and actual upstream call counts,
token usage and billed dollars are unavailable on the unchanged API path.

## What passed

- TXT and Markdown upload reached Ready and persisted parent-child indexing.
- Weekday question used only General; the weekend follow-up retained that scope.
- The comparison supplied both documents and explicitly distinguished the Access
  reservation policy from General's missing reservation requirement.
- Supplied text equals original source slices, with correct line positions;
  evidence fits the configured budget and diagnostics report default settings.
- Refresh restored the exact completed history and scope/ranking diagnostics.
- Citation navigation showed the correct Markdown section and original excerpt.
- Stop produced Interrupted and did not persist an unfinished turn. After refresh,
  only the three completed exchanges remained. Cancellation occurred after the
  Answering status; a first text delta was not recorded, so mid-token cancellation
  is not claimed.
- Both files were deleted. All checked live source, file, parent, child and
  relationship rows plus the file list were empty. Saved evidence/diagnostics
  remained, with deleted labels. New submissions were disabled in the empty library.
- Zero browser JavaScript errors. Both screenshots were visually inspected for
  readable desktop layout and correct evidence/deletion states; no mobile claim.

## Answer and evidence review

[review.json](review.json) retains every expected point and factual claim with
answer quote, source quote, citation and verdict. Codex inspected all three
answers against both supplied evidence and the frozen fixtures. This is implementer
review, not an independent human or separate API judge.

| Question | Expected points | Factual claims | Result |
| --- | --- | --- | --- |
| General weekday hours | Opens 9 AM; closes 6 PM | 2 | Both correct and supported by source 1 |
| Weekend follow-up | Opens 10 AM; closes 2 PM | 2 | Both correct and supported by source 1 |
| Document comparison | Access explicitly requires reservation; General does not specify it | 4 | Both points correct; Access reservation and extra 24-hour detail supported by source 1; General absence and weekend-hours description supported by source 2 |

Six expected points and eight factual claim units pass; all eight claim-citation
pairs support their claims. The comparison quotes the actual reservation rule
and retains the 24-hour qualification. Its General absence wording is page-wide,
but the complete tiny General file is supplied and supports it. This preserves
the known wording limitation on larger documents, rather than establishing general
absence detection. The "only provides" clause is read within the weekend question;
the General fixture also contains weekday hours.

[reviewed-metrics.json](reviewed-metrics.json) is the final complete inventory,
derived without changing the original run. It measures expected-point correctness,
completeness, relevance, faithfulness, citation support/coverage, answerable refusal,
and supplied-evidence coverage. Unanswerable abstention is not applicable.
All four question-specific gold spans are fully supplied. Source spans were derived
afterward from pre-frozen facts; ranking metrics are diagnostic overlap scores,
not pre-registered exhaustive semantic labels or a held-out benchmark.

For selected pre-expansion children at K=5: macro Recall/Hit/MRR/NDCG are 1.0,
Precision is 0.2667 with a fixed K denominator despite fewer results. The tiny
corpus and scope restriction make these scores easy; they establish no improvement
over an alternative configuration. Reranking was disabled.

## Performance and lifecycle measurements

| Measurement | n | Mean | P50 | P95 |
| --- | --- | --- | --- | --- |
| Submit to visible Completed | 3 | 2.826 s | 2.830 s | 3.325 s |
| Retrieval, recorded service stage | 3 | 0.461 s | 0.436 s | 0.513 s |
| Query embedding | 3 | 0.451 s | 0.429 s | 0.506 s |
| Evidence packing | 3 | 0.272 ms | 0.233 ms | 0.420 ms |
| File input to visible Ready | 2 | 1.067 s | 1.067 s | 1.327 s |

P50 is median, P95 nearest rank; these are small sequential samples. Retrieval
includes embedding; stages must not be summed as independent totals. UI timing
includes browser polling. Precise HTTP completion, first answer delta, independent
search/fusion, provider generation timing, queue separation and billed cost remain
unavailable. The index directory occupied 944,292 bytes after ingestion, including
SQLite/WAL and vector-index overhead. This is not marginal bytes per source.
Evidence token counts were 75, 75 and 189. No update operation was exercised.

## Instrumentation gap and warnings

Playwright could not provide any of the four SSE response bodies. The frozen
harness used a generic error, "Response body unavailable after browser
cancellation", even for the three completed requests. That attribution is wrong:
the cause was not captured. Original acceptance.json remains unchanged, and this
review corrects its interpretation. Complete persisted answers, source snapshots,
rankings and exclusions were captured successfully. The future harness now records
the actual exception. No paid rerun was justified solely to repair this observer.

No previous `BoundAsyncStream.__aiter__` finalizer warning appeared in this log;
its cause is still unresolved. One Node color-environment warning is present and
did not affect the workflow. Do not claim a warning-free run or a general fix.

## Artifacts

- [Raw acceptance and saved answers](acceptance.json)
- [Original run and inventory](run.json), [final reviewed inventory](reviewed-metrics.json)
- [Claim and visual review](review.json), [derivation](review.py)
- [Browser log](browser.log)
- [Storage before deletion](storage-before-deletion.json), [after deletion](storage-after-deletion.json)
- [Conversation after deletion](conversation-after-deletion.json)
- [Comparison evidence screenshot](comparison-evidence.png)
- [Deleted historical evidence screenshot](deleted-evidence.png)

This final workflow supports functional closeout. Independent held-out/human
quality review remains open, as listed in the [v1 known issues](../../../docs/v1/known-issues.md).
