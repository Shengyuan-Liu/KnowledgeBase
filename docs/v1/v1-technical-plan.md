# KnowledgeBase v1 Technical Plan

## Scope and Architecture

Status: planned. Implement the [product design](v1-product-design.md) using the
existing React/TypeScript frontend, FastAPI services, SQLite/SQLAlchemy storage,
Chroma vector index, provider interfaces, and ordinary Python orchestration.
API, CLI, and evaluations must use the same retrieval implementation.

Retain the root `knowledgebase/` package. Keep API translation, file lifecycle,
retrieval, provider calls, and storage operations separate. This plan specifies
responsibilities without prescribing a new file for every step.

## Document Representation and Ingestion

1. Accept nonempty UTF-8 `.txt` and `.md` files through the existing upload workflow.
2. Retain the decoded original text as the canonical source in SQLite. This is a
   planned addition: the MVP stores canonical text in chunks rather than a full-document record.
3. Identify source spans and structural metadata. For Markdown, recognize headings,
   paragraphs, lists, fenced code, and tables; preserve heading paths. Do not execute
   code, render raw HTML, or fetch linked resources during ingestion.
4. Create bounded parent regions, then split within each parent to create children.
5. Store parents, children, their relationships, and the chunking configuration.
6. Embed and index children in Chroma; index those same child IDs in BM25.
7. Mark the file Ready only after canonical storage and both retrieval indexes are usable.

Every parent and child belongs to one file. Each child belongs to exactly one
parent and lies within its source range. Record half-open character offsets into
the canonical decoded source, ordering, and heading metadata. Evidence excerpts
must equal their canonical source slices. Derived search text, such as a heading
prefix added for indexing, stays separate from quoted source text.

### Default Chunking

Use Markdown section boundaries where available, then paragraphs and sentences.
Build children from complete sentences up to a token budget; do not cut a word
merely to reach a target size. Configure parent and child limits separately and
record the tokenizer used to measure them.

Oversized sections split into bounded parents. Oversized sentences split at clause
or word boundaries. An indivisible unit exceeding the hard limit requires an
explicit final split, with its source offsets retained. Oversized code blocks split
at lines where possible, and oversized tables at rows; keep their structural
association without presenting synthetic context as original text. Any overlap
must respect source boundaries and remain within the child's parent.

Initial sizes and overlap are experimental settings, not validated defaults.
The existing MVP sizes are character counts; do not treat those numbers as tokens.

### Semantic Chunking Experiment

Within the same bounded parent regions, start from sentences and use their embedding
similarities to propose child boundaries. Respect Markdown structural boundaries
and the same size limits. Do not use prose sentence grouping for fenced code or tables.

Record embedding model, sentence grouping, breakpoint rule, limits, and ingestion
cost. Compare this strategy with structural/sentence chunking while keeping parent
regions and downstream retrieval settings fixed. It is a supported experimental
choice; evidence is required before making it the application default.

## Retrieval Pipeline

1. Preserve the original question. Use recent history only to produce a retrieval
   question for follow-ups, retaining the original question for answer generation.
2. Select Ready file IDs from SQLite. Both retrieval routes restrict candidates to
   eligible children before truncating their result lists.
3. Retrieve lexical candidates with BM25 and semantic candidates with Chroma.
   Use the same retrieval question and child identity in both routes.
4. Merge candidates by child ID with RRF and retain a bounded fusion window.
5. Rerank the fused children against the retrieval question with a relevance model.
6. Select a bounded number of children and load their canonical parents.
7. Deduplicate parents by ID, rank each by its best selected child's rerank position,
   and retain all selected child associations. Use stable IDs to break remaining ties.
8. Pack whole parents in that order within an evidence token budget. Skip a parent
   that does not fit rather than silently truncating its evidence; record exclusions.
9. Assign source numbers to the included parents and generate a grounded answer.
10. Check source-number membership and persist the completed answer and evidence snapshot.

Configure the parent limit so a single parent fits the evidence budget, allowing
for citation labels and metadata. The total prompt budget must also leave room
for instructions, the question, and the model's output. If no parent is included,
use the existing insufficient-evidence behavior.

This child-rerank-then-expand ordering is the v1 starting design. It keeps reranker
inputs focused but can miss relevance that becomes apparent only in broader
context. Record this limit; change ordering only in a separately labeled experiment.

### BM25 and RRF

Use a small lexical adapter with build/update, eligible search, and file deletion
responsibilities. Choose its library during implementation based on this local
workload; Elasticsearch is not required. Tokenization must be explicit and tested
on course identifiers, abbreviations, and punctuation in the actual corpus.

Persist the lexical index or deterministically rebuild it from canonical children
before serving queries. Document the selected lifecycle. An in-memory scorer is
acceptable for the local corpus if additions, deletions, and restart are correct.

For child `d`, use `RRF(d) = sum(1 / (k + rank_r(d)))` over routes containing it,
with one-based ranks and zero contribution from a missing route. Deduplicate
within each route. Keep `k`, each route's candidate limit, the fusion window, the
rerank selection limit, and the final context budget as distinct settings.

Record raw BM25 scores, vector distance, route ranks, and fusion scores separately.
Their scales and meanings differ; none is a correctness probability.

### Reranker

Use a narrow query-plus-candidates interface returning scores tied to child IDs.
Select a local or API-based model during implementation using measured quality,
latency, input limits, and operating cost. Preserve the full scored input in run
metadata or a reproducible representation; do not silently truncate it.

Include the heading path when useful and consistently available, separating it
from canonical excerpt text. Record model and input formatting. An enabled
reranker failure surfaces through existing error handling; do not silently label
an unreranked answer as a successful full-pipeline result. A deliberately disabled
reranker is a named evaluation configuration.

## Evidence and Storage Contracts

| Record | Required information |
| --- | --- |
| File/source | ID, filename, format, state, canonical decoded text, source hash, indexing configuration |
| Parent | ID, file ID, order, source offsets, exact text, heading path |
| Child | ID, parent ID, file ID, order, source offsets, exact text, derived index text if used |
| Candidate trace | Child ID, available route scores/ranks, RRF rank/score, rerank rank/score |
| Final evidence | Message-local source number, parent/file identity, exact supplied excerpt, location, selected child associations |
| Saved answer | Original question, answer, final evidence snapshot, citation diagnostics, recorded retrieval configuration |

These are logical requirements; they do not prescribe separate database tables
for every record. Keep ORM objects within storage and expose application snapshots.

Numbered citations refer to the parent excerpts actually supplied to generation.
Child hits explain selection in diagnostics. A source may be supplied but not cited;
the UI must distinguish those states. Citation membership checks do not validate
claim support or quotation fidelity.

Preserve the existing Ready-only and deletion ordering invariants across both
indexes. Make a file ineligible before removing lexical entries, vectors, children,
parents, and its canonical source. Partial ingestion and deletion cleanup must cover
both indexes. Historical answer snapshots survive deletion. SQLite and the indexes
do not form a shared transaction.

Keep the existing single-process data-directory ownership, interrupted-upload
recovery, stream completion, cancellation, and completed-turn persistence behavior.

## Configuration and Existing Data

Extend the existing Settings and `.env.example`; keep credentials in ignored `.env`.
Record effective configuration in each run. Chunking, parsing, embedding, and index
text changes require reindexing. Query candidate limits and rerank settings normally
do not, but remain part of the evaluation configuration.

For v1 development, build a fresh isolated data directory from original files and
keep the MVP directory intact. Do not interpret old flat chunks as a parent-child
index or silently rewrite the user's library. Existing conversations remain
accessible using the MVP directory; automatic history migration into a fresh v1
directory is outside this plan. Define and verify any later local-library transition
separately before switching the running application.

## Implementation Sequence

| Stage | Deliverable | Verification focus |
| --- | --- | --- |
| 1 | TXT/Markdown source representation and structural sentence chunks | Exact spans, heading paths, oversized units, upload/delete behavior |
| 2 | Parent-child storage and vector retrieval with parent expansion | Relationships, deduplication, context budget, saved evidence |
| 3 | BM25 plus RRF over child IDs | Route eligibility, lexical fixtures, fusion ordering, restart and cleanup |
| 4 | Reranker integration | Identity mapping, scored input limits, end-to-end diagnostics |
| 5 | Semantic child-chunking strategy | Controlled comparison with the structural strategy |
| 6 | Frontend integration and release evaluation | Real-provider workflows, held-out review, latency and cost |

Add relevant tests with each implemented stage and commit each completed change.
This documentation does not authorize writing Python implementation beyond the
project's [ownership rules](../../AGENTS.md).

## Technical References

- [Elastic: RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) explains rank-based fusion.
- [Elastic: ranking and reranking](https://www.elastic.co/docs/solutions/search/ranking) describes candidate generation and subsequent ranking.
- [LangChain: Markdown splitting](https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter) illustrates heading metadata.
- [LlamaIndex: semantic splitting](https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/semantic_splitter/) describes embedding-based sentence grouping.

These references explain techniques; they do not require adopting those frameworks.
