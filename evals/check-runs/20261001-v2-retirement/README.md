# v2 Branch Retirement

Date: 2026-10-01. Reviewer: Codex. Starting code revision: `1ca2300`.
The user explicitly requested merging `v2`, deleting it and pushing the result.
This authorizes the remaining v2 commits and local/remote branch retirement;
it does not establish a new development version or authorize future merges.

## Scope and review

- Updated AGENTS.md, the project README and the v2 index to remove instructions
  to continue using the retired branch. Historical implementation/evaluation
  reports retain their original approval status and branch names.
- Reviewed the changed prose for English content, consistent branch lifecycle,
  valid local links and Markdown formatting. The working checkout was clean
  before these documentation changes.
- Fetched remote refs before merging: remote main and remote v2 had no commits
  absent from local v2. There was one worktree, the current checkout, and no
  other active task using this repository in the inspected task inventory.
- Merge without rewriting history. Verify the retired branch tip is an ancestor
  of main before deletion; push main and the remote deletion together with a
  lease on the fetched remote v2 tip. Verify final local and remote refs.
- No application code, dependency, configuration, corpus or model changes.
  The prior verified code remains `1ca2300`: 868 backend tests passed, one
  opt-in live test skipped, and 21 controlled browser tests passed. See the
  [layering verification](../20261001-layered-architecture/README.md).
- No new automated application tests or paid evaluations were run for this
  documentation and Git operation. Test duration/counts, model identity,
  concurrency and performance measurements are not applicable to this review.

## Metric inventory

Every item below has status `not_applicable`, value `null`, no samples and no
aggregation: this operation reviews documentation and preserves Git history,
without executing retrieval, generation, ingestion or a performance workload.

| Metric | Status |
| --- | --- |
| Recall@K | not_applicable |
| Precision@K | not_applicable |
| Hit Rate@K | not_applicable |
| MRR | not_applicable |
| NDCG@K | not_applicable |
| Final evidence coverage | not_applicable |
| Answer correctness | not_applicable |
| Faithfulness | not_applicable |
| Answer completeness | not_applicable |
| Answer relevance | not_applicable |
| Citation support | not_applicable |
| Citation coverage | not_applicable |
| Abstention | not_applicable |
| First-answer-delta latency | not_applicable |
| Complete-response latency | not_applicable |
| Stage latency | not_applicable |
| Token usage and cost | not_applicable |
| Reliability | not_applicable |
| Concurrency and throughput | not_applicable |
| Ingestion and index | not_applicable |
