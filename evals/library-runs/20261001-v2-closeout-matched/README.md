# Initial closeout replay: retained failures

Product version: `d8108df`, on `v2`. All six requests complete and all 13 requested
positive facts match the original references, but only **5/6 case gates pass**.
Correct numbers do not override unsupported citations.

The NVIDIA answer supplies the right four amounts but cites a page-8 continuation
without its page-7 period headers and units. Only the quarterly non-GAAP fact has
a separately supporting full table. Semantic supplied-evidence coverage is 9/13;
10/14 emitted factual groups are supported (including one additional RAG training
statement). Exact reviews are in [review.json](review.json), separate from
[retrieval/timing diagnostics](diagnostics.json) and [all 20 metrics](measurement.json).
The 13/13 correctness figure must not be described as full acceptance.

A separately frozen [synthetic dependency case](../../materials/pdf-v2-closeout-dependency/protocol.json)
retrieves an explicit laboratory identity, but the binder returns `missing` because
the final calibration interval is absent. The delivered answer contains 1/2 facts.
Its exact request, decisions and final answer remain in
[the first dependency output](dependency/unknown-laboratory-planned.json).
The fixture is fictional controller evidence, not a natural-document quality score.

The two observed failures motivate the
[continued-table and binding repair](../../check-runs/20261001-v2-closeout-fixes/README.md).
The [final release replay](../20261001-v2-release/README.md) retains the same original
questions, PDF bytes and index before comparing the repair. Historical outputs
are unchanged. Both the matched and synthetic failures remain visible.

The isolated index was copied from `data/evals/20261001-new-pdf-acceptance-2` to
`data/evals/20261001-v2-closeout-matched`; user data and `.env` were unchanged.
The first six requests use exactly the same original file IDs and frozen labels.
The two synthetic PDFs were uploaded afterward. No paid judge or automatic retry
was used. Reviewer: Codex model, not a human.

Command records preserve durations, source hashes, failures and metric applicability.
The owned server was stopped before its index was copied into the final run.
