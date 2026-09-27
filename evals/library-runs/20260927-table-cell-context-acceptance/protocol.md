# Explicit table cell readings: matched six-request acceptance

Repeat the exact three questions in both modes from the [previous run](../20260927-table-context-scope-acceptance/README.md).
The [questions](frozen-cases.json), [source-page gold](frozen-gold.json),
[index-bound facts](frozen-fact-labels.json) and [original scoring rubric](frozen-original-protocol.md)
remain byte-identical. The previous result was 19/24 requested points, including
incorrect grouped-column values and fabricated zeros for blank cells.

## Frozen workload

Clone the stopped previous isolated index under its owner lock. Retain original
PDF bytes, extraction, child/parent chunks, embeddings and historical conversations.
No upload, reparse or re-embedding. Verify source-directory hashes before and after;
all six requests start new conversations. Commit product code on v2 before launch.
Freeze code, safe runtime settings and the .env hash; never record credentials.

Run exactly six HTTP/SSE requests, once each, in the existing order: dense
single/planned, state totals planned/single, grouped and blank cells single/planned.
Keep GPT-4.1, text-embedding-3-small, BGE reranking, K=5, hybrid retrieval, the
4,096-token context budget and planned-search limits. Use concurrency one, port
8786, provider timeout 180 seconds, client timeout 240 seconds and zero retries.
No paid judge, full evaluation or automatic answer rerun. Record actual revisions,
all SDK payloads/usage, rankings, exclusions, supplied evidence, responses and history.

Only the model-facing table representation changes: complete supplied values bind
to full parent/leaf column paths within labeled rows; null denotes an extracted
empty cell. Original excerpts, cell coordinates and physical page provenance remain.
Plans, rankings and admitted source sets may vary; retain actual trajectories.

## Scoring and review limitation

Keep the original 0/0.5/1 requested-point and paragraph/bullet claim-group rubric.
Review all 24 points and all factual groups against original-page gold, actual SDK
contexts and citations. Distinguish empty cells, zero and unavailable excerpts.
All questions are answerable; report incorrect refusals separately from uncertainty.
Use the same functional gates: six completions, all points correct/complete, all
claims supported/cited, correct row/group/blank distinctions and saved-history parity.

This run has one Codex reviewer and a separate mechanical source/provenance audit.
The earlier runs used two independent Codex reviewers; that review procedure cannot
be reproduced in this single-agent turn. Record this limitation explicitly. Do not
call the mechanical audit an independent semantic review or human review. Report
functional gates and the missing independent review separately, even if all facts
are correct. No human acceptance or merge is implied.

## Measurements and commands

Follow the [measurement policy](../../measurement-policy.md): retain all 20 metrics,
raw evidence and failed attempts. Measure first answer delta, complete response and
stage latencies separately, with samples, means and percentiles. Record SDK token
usage; billed cost remains unavailable without billing data. Index copy is local
preparation, not ingestion performance. Sequential throughput is not load capacity.
One sample per case/mode on development questions cannot establish generalization.

After offline regression checks and the product commit, run clone_index.py,
verify_harness.py, prepare.py, start_server.py, run.py and stop_server.py through
record_check.py using unique record names. The recorder takes scope, name and
command; offline is for preparation/checks and live for server/request lifecycle.
Always stop the owned server and verify index/history integrity after requests.
