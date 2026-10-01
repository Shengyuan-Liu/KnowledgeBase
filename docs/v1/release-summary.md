# KnowledgeBase v1 Release Summary

As of 2026-09-26, the user-approved v1 implementation is merged locally into
`main` at `483a156`. The default functional release is delivered. The final
real-provider browser workflow also passes on the same product code. The user also explicitly authorized merging the subsequent release summary and
final browser closeout evidence on 2026-09-26. This authorization covers closeout
commits `360a982` and `55837b0` plus this status update; it does not imply a remote push.

v1 improves the local, single-user, English-only knowledge base from basic TXT
vector search into source-preserving TXT/Markdown retrieval with structured
context, hybrid search, document scope, and inspectable evidence. Its development
experiments establish specific observations, not general accuracy superiority.
Independent held-out quality evaluation and human review remain outstanding.

## What v1 added

| Area | Delivered behavior | Implementation and evidence |
| --- | --- | --- |
| TXT and Markdown parsing | Canonical source text, structural blocks, headings, exact character offsets and original line locations; connected to uploads, CLI and evaluation | [Parsing](../document-parsing.md), [storage](../document-storage.md) |
| Structural chunking | Group compatible blocks and split oversized material at structure/sentence boundaries under token budgets; preserve exact source slices | [Structural chunking](../structural-chunking.md) |
| Parent-child indexing | Retrieve small children, expand to bounded parents, preserve child/parent associations and deduplicate supplied context | [Chunking](../parent-child-chunking.md), [storage](../parent-child-storage.md), [retrieval](../parent-child-retrieval.md) |
| Hybrid retrieval | Combine BM25 keyword and vector candidates using reciprocal rank fusion; retain route scores and rankings | [BM25](../bm25.md), [RRF](../rrf.md), [hybrid retrieval](../hybrid-retrieval.md) |
| Evidence packing | Enforce a context token budget including source labels; admit parents, use remaining room for whole selected children, and record exclusions | [Parent-child retrieval](../parent-child-retrieval.md) |
| Document scope | Resolve supported explicit document references or API file IDs before retrieval; preserve representatives for multi-file comparisons when capacity permits; retain scope diagnostics | [Document scope](../document-scope.md) |
| Grounded answer prompts | Request claim-local citations, faithful qualifications and source behavior, question-focused answers, and an explicit item for each named comparison document | [Answer grounding](../answer-grounding.md) |
| Evidence UI and history | Markdown uploads, heading paths, line ranges, parent/child identity, citation status, candidate rankings, scope and budget diagnostics; retain evidence after refresh and source deletion | [Frontend design](v1-frontend-design.md), [final browser acceptance](../../evals/browser-runs/20260926-v1-final-ui-1/README.md) |
| Optional local reranking | Bounded local BGE cross-encoder scoring before selection; child and experimental parent scoring with recorded cost/coverage tradeoffs | [Reranking](../reranking.md) |
| Experimental semantic chunking | Embedding-based sentence boundaries within unchanged structural parents, with persisted settings and traces | [Semantic chunking](../semantic-chunking.md) |
| Evaluation and diagnosis | Frozen comparisons, source-span coverage, claim/point review, separate retrieval and answer metrics, explicit missing measurements, retained failures, stage timing and dual-clock sleep diagnosis | [Metrics](../../evals/metrics.md), [measurement policy](../../evals/measurement-policy.md), [diagnosis](../../evals/check-runs/20260926-generation-diagnostics/README.md) |

File management, streaming answers, Stop, continued conversations, saved history,
and source inspection already existed in the MVP. v1 extends and verifies these
workflows against the new source, retrieval and evidence representations; it does
not claim to have introduced them from scratch. See the [MVP report](../../evals/analyses/2026-09-21-mvp-release.md).

## Default execution path

1. Decode TXT/Markdown and preserve source blocks and locations.
2. Build structural parents and children; store source metadata and index children.
3. Resolve the question and any supported document scope.
4. Search eligible children with BM25 and vectors; fuse their ranked lists.
5. Select children, expand/deduplicate parents, and pack labeled evidence to budget.
6. Generate a grounded answer, stream it, and save the completed answer with its
   exact supplied evidence, citation diagnostics and retrieval record.
7. Let the user inspect the evidence now or from restored history.

| Setting | Shared default |
| --- | --- |
| Chunking strategy | `parent_child` with structural sentence boundaries |
| Child / parent budgets | 512 / 1536 tokens, `cl100k_base` |
| Retrieval | `hybrid`, fused candidate limit 20, top-K 5 |
| Fusion | RRF constant 60; BM25 k1 1.2, b 0.75 |
| Evidence | 4096 tokens, `parent_then_child` packing |
| Answer / embedding models | `gpt-4.1` / `text-embedding-3-small` |
| Reasoning effort | Omitted by default |
| Reranking | Disabled; configured scoring unit is child |

These are [shared defaults](../../knowledgebase/config.py); local environment
settings can override them. The final browser run explicitly froze its settings
and used a separate data directory. Changing chunking affects new uploads;
existing documents need reindexing to adopt new boundaries. Changing the embedding
model requires a fresh compatible index. See [configuration](../configuration.md).

## Implemented experiments that are not promoted defaults

- **Local reranking:** available, but off by default. Bounded local compute and
  ranking changes do not establish a universal quality gain.
- **Semantic chunking:** opt-in. The [paired comparison](../../evals/library-runs/20260925T002400Z-semantic-acceptance/README.md)
  found two substantive evidence regressions. The [parent-scoring/packing experiment](../../evals/library-runs/20260925-parent-reranking/README.md)
  recovered them with more compute/context; that does not justify changing defaults.
- **Parent scoring and alternative packing:** retained as measured options with
  configuration-specific evidence, rather than advertised as universally better.
- **LLM judging:** a structured assessment tool, not ground truth. The
  `claim-inventory-v11` protocol retains calibration disagreement and invalid
  reviews. The [review supplement](../../evals/library-runs/20260925-review-supplement-3/README.md)
  has 23/24 valid assessments; validity is not correctness.

## Acceptance evidence

| Check | Recorded result | Scope and limitation |
| --- | --- | --- |
| Backend checks before merge | 593 passed, 1 intentionally skipped; subsequent cleanup checks 12 passed, including 25 mock-HTTP real-SDK streams | [Check records](../../evals/check-runs/20260926-generation-diagnostics/README.md); not rerun for this documentation closeout |
| Earlier frontend checks | 42 unit tests and 12 distinct browser scenarios passed across retained runs | [Scope records](../../evals/check-runs/20260925-document-scope/README.md); these are earlier results, not a new aggregate run |
| Frozen default service acceptance | 11/11 requests and strict reviews passed; 26 factual claim units supported; all annotated evidence covered in 7 answerable cases | [Awake-host acceptance](../../evals/library-runs/20260926-comparison-awake/README.md); development sample and Codex review |
| Final real-provider browser workflow | 1/1 workflow passed; 3/3 completed answers meet frozen requirements; Stop, refresh and both deletions pass | [Browser report](../../evals/browser-runs/20260926-v1-final-ui-1/README.md); two tiny synthetic files, no load or held-out quality claim |
| Closeout build and documentation | TypeScript/build pass; content, local links and formatting reviewed | [Closeout record](../../evals/check-runs/20260926-v1-closeout/README.md) |

Service acceptance mean completion was 1.757 s, P95 completion 4.016 s, and P95
first answer delta 3.596 s. Final browser submit-to-visible-completion mean was
2.826 s, P95 3.325 s across three answers. These measure different boundaries and
workloads; they are not a before/after performance comparison. Browser first delta,
actual provider usage/cost and provider model revisions were not exposed.

The final UI check verified exact source slices/lines, scoped follow-up, both
comparison documents, persisted diagnostics, cancellation without a saved partial
turn, and live source/index-row cleanup with historical evidence retained. The two
screenshots were visually reviewed. No browser JavaScript error or prior stream
finalizer warning appeared in this attempt. Raw SSE bodies could not be obtained
by Playwright; the preserved observer message incorrectly attributes this to
cancellation even for completed requests. The report discloses that harness
limitation; saved complete answers and evidence remain available.

## Known limits and remaining work

The [known-issues register](known-issues.md) separates unresolved runtime behavior,
wording limits, experimental regressions and independent-validation gaps.

The bounded functional v1 scope is complete and accepted. Fully independent
quality validation is **not complete**: a genuinely separate frozen release
population and independent human review are still needed before claiming broad
release accuracy or general superiority over the MVP. More development sampling
must not be renamed held-out validation. The stream finalizer warning also remains
unresolved despite no observed failed request in its recorded occurrence.

PDF/OCR, remote ingestion, agents, multi-user accounts, hosted deployment and load
capacity are outside this v1 scope. Development has moved to `v2`; `v1` is retired
because its commits are preserved in `main`. Future work uses the active version
branch, with separate user approval for each merge.

## Delivery history

- `282158a`: Markdown ingestion merged.
- `cd10620`: parent-child and hybrid retrieval merged.
- `483a156`: user-approved remaining retrieval, evidence, experiment and evaluation
  work merged locally on 2026-09-26.
- `360a982`: froze final browser acceptance on `v1`; product code stayed identical
  to the accepted merge. Later closeout commits retain results and this summary.

Historical failed attempts, timeout recovery and prompt/evidence regressions are
preserved in their original run directories. This summary changes no historical
scores and introduces no new product implementation.
