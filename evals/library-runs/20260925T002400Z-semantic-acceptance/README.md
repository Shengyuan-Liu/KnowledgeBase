# Paired semantic child-chunking acceptance

Recommendation: retain structural `parent_child` as the default and keep
`semantic` experimental. Semantic chunking is operational and passed the
[live browser workflow](../../browser-runs/20260925-semantic-ui-1/README.md), but
lost substantive evidence on two development questions and increased ingestion
work. Neither a working UI nor aggregate judge scores authorize feature acceptance
or merging into `main`.

## Scope and controls

The [plan](PLAN.md), [resolved configuration](plan.json), [24 questions](cases.json),
[17-document manifest](corpus.json) and [604 canonical parser blocks](blocks.json)
were frozen before collecting either batch. Eighteen questions are existing
development/regression cases; six were newly authored by Codex on the same familiar
corpus and are reported separately. They are not independently labeled human
questions or a new release data population. No tuning or answer regeneration was
performed after observing results.

Production code was unchanged during collection, identified by the per-file
digests in each `run.json`; the frozen harness was committed at `f13847a`.
All 38 parent regions match in filename, original offsets, text and token count
across the two strategies. Models and settings are fixed: GPT-4.1 (returned
revision `gpt-4.1-2025-04-14`), text-embedding-3-small, hybrid BM25/vector retrieval,
20-candidate limits, local BAAI/bge-reranker-v2-m3 on MPS (revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`), top-k 5, 512-token children,
1536-token parents, 4096-token formatted evidence budget and parent-then-child
packing. The provider did not return an immutable embedding revision.

The semantic strategy uses adjacent-sentence cosine threshold 0.5 and batches of
32. It also retains paragraph boundaries, while the structural control can pack
paragraphs together. This compares the complete strategies, not the isolated
effect of cosine splitting. There were 166 semantic break decisions among 363
adjacent pairs. Children grew from 92 to 778; mean child length fell from 284.8 to
33.9 tokens. Finer retrieval units can compete for the same fixed top-k budget.

## Source coverage and answer inspection

Primary retrieval comparison uses the same gold source spans on 21 answerable
questions. The three unanswerable questions have no gold spans and are excluded
from retrieval averages, not scored as zero.

| Gold source metric | Parent-child | Semantic |
| --- | ---: | ---: |
| Supplied character coverage, all answerable (21) | 99.967% | 95.205% |
| Supplied character coverage, old development (16) | 99.957% | 93.707% |
| Supplied character coverage, newly frozen (5) | 100% | 100% |
| Fully covered gold-span fraction, all answerable (21) | 76.190% | 71.429% |

Character coverage averages the union-covered fraction of each gold span within
a question, then macro-averages questions. Full-span coverage is not a count of
correct answers: five DeepSeek cases lose only separator newline characters in
both modes. Their actual factual text remains supplied. Exact missing characters
are retained in [collection-audit.json](collection-audit.json).

The two substantive regressions are `msds-working-enrollment` (summer enrollment
exception omitted) and `msds-cpt-source-context` (admissions FAQ internship timing
omitted). Each drops from complete to 50% supplied gold coverage. The semantic
answers acknowledge missing information and fail to answer all requested parts.
One loses useful candidates at top-k selection; the other already lacks its FAQ
span in the candidate window. Parent expansion cannot recover an unselected
parent. [REVIEW.md](REVIEW.md) records both paired inspections, all twelve new-case
answers, and judge caveats against exact supplied excerpts.

Stage traces distinguish vector candidates, lexical candidates, fused candidates,
reranked top five, selected children and packed evidence. The same 21 answerable
questions give these macro-averaged gold character coverage values; candidate
windows use their full recorded limits and top-five rows use five children:

| Stage | Parent-child | Semantic |
| --- | ---: | ---: |
| Vector candidate window | 99.447% | 79.817% |
| BM25 candidate window | 99.180% | 75.397% |
| Fused candidate window | 99.632% | 84.271% |
| Reranked / selected top-five children | 93.799% | 71.101% |
| Final supplied evidence | 99.967% | 95.205% |

Parent expansion recovers substantial text in both modes, but does not restore
all of semantic's lost source coverage. Raw child-based ranking
metrics remain in each summary but their deltas are withheld because boundaries
changed. Secondary Recall/Precision/Hit Rate/MRR/NDCG@5 project hits onto unique,
immutable parser blocks, ordered by child rank and then source order within each
hit. Binary gold overlap is an incomplete relevance proxy. This induced ordering
is not a separately scored block retrieval system and cannot establish general
ranking quality; broad early hits can place headings before a relevant block.

## Frozen v11 answer assessment

Each saved batch was judged once with `claim-inventory-v11`, its frozen source
hash, GPT-5.4-mini (returned revision `gpt-5.4-mini-2026-03-17`), high reasoning,
four workers and no retries. All 48 reviews completed with valid structure; none
are pending. A valid review is still an LLM assessment, not ground truth.

| Assessment, all 24 questions per mode | Parent-child | Semantic |
| --- | ---: | ---: |
| Expected-point correctness, macro-average | 100.00% | 97.22% |
| Expected points attempted, irrespective of truth | 100.00% | 98.61% |
| Supported factual-claim fraction, macro-average | 95.57% | 95.89% |
| Claim-local citation coverage, macro-average | 66.12% | 62.33% |
| Answer relevance, normalized rubric | 100% | 100% |
| Strict passes: all required points, claims and citations | 9/24 | 7/24 |
| Appropriate abstention on unanswerable cases | 3/3 | 3/3 |
| Unjustified abstention despite sufficient supplied evidence | 0/21 | 0/21 |
| Any full/partial abstention on answerable cases | 0/21 | 2/21 |

The semantic partial refusals are caused by missing retrieval, so they appear in
the last row without increasing unjustified abstention. A stated refusal may
count as an attempted point while receiving correctness zero; “points attempted”
is not successful answer completeness. Expected-point correctness is not overall
accuracy and does not capture unsupported extra claims. Citation support averages
95.51% over 23 applicable control answers and 96.76% over 22 semantic answers;
unequal applicability prevents treating those aggregates as a clean improvement.
The comparison file also retains the identical-case, applicable-on-both-sides
subset with explicit sample counts.

| Split | Expected-point correctness, control / semantic | Claim-local citation coverage, control / semantic | Strict passes, control / semantic |
| --- | ---: | ---: | ---: |
| Existing development, 18 | 100% / 96.30% | 63.74% / 62.87% | 6/18 / 4/18 |
| Newly frozen, 6 | 100% / 100% | 73.24% / 60.71% | 3/6 / 3/6 |

The same familiar corpus, model-authored questions and known v11 classification
issues limit interpretation. The [source review](REVIEW.md) retains a disputed
self-description penalty and advice-classification issues. It also confirms a
semantic `api-thinking` overstatement: “only effort is supported” does not prove
that every other value is ignored. Extra advice on where to find a personal
assignment is not grounded by the corpus. Scores were not edited to match the
reviewer's interpretation.

## Performance and ingestion

Both RAG batches ran sequentially at concurrency 1 with SDK retries disabled.
Each mode completed 24/24 requests, with zero request errors, timeouts or retries.
The control ran first, with no warmup. Host/provider load and caches were not
controlled. These are descriptive single-pass measurements, not load capacity or
causal speedup evidence.

Timings are seconds, n=24 per mode, mean / median P50 / nearest-rank P95. Service
timing begins at the in-process production request and ends after iterator
completion/persistence. HTTP transport is excluded. Query embedding, reranking
and packing are parts of retrieval; do not add them to retrieval a second time.

| Stage | Parent-child | Semantic |
| --- | ---: | ---: |
| Request to first answer delta | 3.708 / 3.761 / 4.216 | 1.788 / 1.841 / 2.268 |
| Complete response | 4.831 / 4.927 / 6.221 | 2.807 / 2.756 / 3.776 |
| Retrieval | 3.071 / 3.123 / 3.375 | 1.158 / 1.083 / 1.762 |
| Query embedding | 0.215 / 0.204 / 0.308 | 0.204 / 0.191 / 0.272 |
| Local reranking | 2.832 / 2.896 / 3.159 | 0.902 / 0.747 / 1.527 |
| Evidence packing | 0.0027 / 0.0023 / 0.0052 | 0.0017 / 0.0012 / 0.0040 |
| Generation | 1.752 / 1.716 / 3.087 | 1.644 / 1.397 / 2.750 |

The observed latency difference is concentrated in local reranking, consistent
with shorter child inputs; this is an interpretation, not a controlled causal
attribution. Reranker constructor loading took 4.513 versus 1.617 seconds, measured
once each and excluded from request timings. Separate search/fusion latency and
independent queue-wait durations are unavailable.

| Ingestion / provider observation | Parent-child | Semantic |
| --- | ---: | ---: |
| Corpus upload-to-searchable time (17 files) | 8.510 s | 21.483 s |
| Index bytes before queries | 2,418,852 | 8,681,636 |
| Ingestion embedding calls | 17 | 43 |
| Ingestion embedding tokens | 26,199 | 42,026 |
| Of those, sentence-scoring tokens | No sentence calls | 15,679 |
| Query embedding tokens (24 calls) | 567 | 567 |
| Answer input / output tokens (24 calls) | 81,734 / 3,693 | 65,637 / 3,330 |
| Judge input / output tokens (72 calls) | 331,997 / 356,914 | 304,025 / 299,987 |

These are provider-returned usage values, not estimated bills. Billed dollars are
unavailable. Local reranking is local compute; no paid reranker call occurred.
Per-file upload times, boundary inputs, call assignments and source snapshots
are retained. The paired corpus run does not exercise update/delete; deletion
and preserved historical evidence are verified in the separate browser run.
Judge review duration (three stages per question, excluding worker queue wait)
was mean/P50/P95 78.816/61.402/234.234 seconds for control and
55.196/46.045/156.073 seconds for semantic, n=24 each. Judge work is excluded from
RAG latency. Output-token totals include the provider's returned reasoning usage;
they are not merely the visible assessment text.

## Reliability and remaining acceptance limits

The collection log contains one ignored `Response.aiter_raw` cleanup exception,
`ValueError: async generator already executing`, between two semantic question
completion lines. All 48 answer records have complete events and every generation
call has successful completion, usage and deltas. No answer loss was observed,
but the cleanup cause is unresolved and the warning remains visible. It did not
recur in the live browser run. No paid rerun was made merely to remove the warning.

The next focused work is claim-local citation placement and multi-part retrieval
coverage. Retain this frozen experiment as a regression record. A later component
change requires its own completed-feature comparison; do not tune the judge or
rerun expensive benchmarks after each intermediate edit. Independent human review
and a broader independent release set remain outstanding.

## Artifacts and checks

- `parent_child/` and `semantic/`: code/settings, complete answers and streaming
  events, exact supplied sources, prompts/provider calls, child/parent snapshots,
  judge inventories/assessments, full metric inventories and split summaries.
- [paired comparison](comparison.json): every case's improvements/regressions,
  compatible deltas and applicable paired quality subsets.
- [fixed-block comparison](fixed-block-comparison.json): the complete secondary
  Recall/Precision/Hit Rate/MRR/NDCG@5 inventory for all six stages and all splits;
  each mode's `stage-coverage.json` retains underlying block IDs and gold spans.
- [analysis execution](analysis-run.json): exact offline postprocessing command,
  code version, duration and successful identical-parent verification.
- [collection-audit.json](collection-audit.json): streamed completion and usage
  audit, exact whitespace gaps, input-call assignment and warning. It is a
  timestamped snapshot taken while judging was active; final judge usage is in
  the final summaries and complete calls, not this intermediate audit.
- [REVIEW.md](REVIEW.md): Codex source inspection, explicitly not human ground truth.
- [preflight record](preflight-1.json): frozen inputs checked, 3 tests passed.
- [analysis check](analysis-check-1.json): input and stable-block projection
  checks, 4 tests passed.
- [browser build](browser-build-1.json): frontend typecheck and production build passed.
- [final artifact audit](final-audit-2.json): 21 checks passed, including frozen
  protocol/questions, exact answer-to-review hashes, source slices, local links,
  whitespace and absence of the authorized credential in saved artifacts.
  [Attempt 1](final-audit-1.json) is retained: its checker initially hashed only
  answer text although the existing judge hashes the full answer record. The
  checker was corrected; no answer or review was changed and no API call repeated.
- [real browser acceptance](../../browser-runs/20260925-semantic-ui-1/README.md):
  one passed workflow, two grounded questions, restored diagnostics and deleted history.

Provider credentials came from the authorized existing `.env`; neither credentials,
the existing library nor local configuration were modified. All changes remain
on `v1`; no merge was performed.
