# Semantic chunking development verification

This is an offline implementation check, not a live RAG quality result. No paid
provider requests ran. Structural parent-child chunking remains the default.

- [Targeted checks](targeted-1.json): 159 passed.
- [Initial backend check](backend-1.json): 537 passed, 2 failed, 1 skipped. The
  failures were exact table inventories that needed the new `document_indexes`
  table; both were updated, with a legacy-source compatibility check added.
- [Final backend check](backend-2.json): 540 passed, 1 skipped. The opt-in live
  API test is skipped. An existing dependency deprecation warning remains.
- [Runner startup failure](runner-import-failure.json): no tests started; the
  retry sets `PYTHONPATH=.`. Failed attempts remain retained.

Each JSON records command, code identity, duration, counts, raw-output path and the
complete metric inventory. Live quality, provider cost and production latency
are not applicable to these mocked checks.

## Controlled behavior comparison

`tests/test_semantic_chunking.py` constructs structural and semantic children from
the same frozen inline sources, parent/child budgets and tokenizer. Parent records
are identical. With fixed vectors [1,0], [1,0], [0,1], the three-sentence fixture
changes from one structural child to two semantic children at the topic change.
No sentences are lost or rewritten. Equal-threshold pairs stay together;
token-budget splits still apply when all similarities are equal. Code/table/list
spans match the structural control, including CRLF and Unicode fixtures.

The upload check verifies 1 parent / 2 children, two bounded sentence-embedding
batches, separately indexed child vectors, recorded threshold/model, and cascading
deletion. API JSON/SSE configuration tests exercise both strategies, and legacy
source tests verify additive schema initialization without inventing old settings.

These are boundary and lifecycle comparisons with synthetic vectors. Retrieval
quality, answer correctness, citation support, streaming latency, provider token
usage and billed cost cannot be inferred from them. A live paired source-span
comparison remains part of feature acceptance, with the judge held at v11.

Documentation review: linked local files resolve, configuration and default
claims match the implementation, and `git diff --check` passes. No merge is
authorized by these results.
