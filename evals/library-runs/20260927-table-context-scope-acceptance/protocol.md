# Table context and quoted scope: matched six-request acceptance

This run repeats the exact six question/mode pairs from the
[failed baseline](../20260927-dense-table-acceptance/README.md). The
[questions and original annotations](frozen-cases.json),
[original review protocol](frozen-original-protocol.md),
[source-page gold](frozen-gold.json), and
[index-bound fact labels](frozen-fact-labels.json) are byte-identical copies of
the baseline inputs. The immutable [baseline rubric](../20260927-dense-table-acceptance/protocol.md)
governs all requested-point, claim-group, citation, blank-cell and abstention
judgments. This addendum changes index preparation and comparison only.

## Frozen comparison and preparation

Copy the stopped baseline's isolated data directory under its exclusive ownership
lock into a new directory. Preserve every original PDF, database, embedding index,
extraction, child, parent and historical conversation. Retain a complete byte-hash
manifest and database-table counts/hashes. Verify the source directory is unchanged
after copying and after the live run. Do not upload, parse or re-embed the PDF.
Ingestion time and ingestion provider usage are not applicable in this run; local
copy time is preparation overhead, not ingestion performance.

Before requests, verify the copied index's production snapshot matches the frozen
baseline file identity, extraction, chunks and parents exactly. All six requests
start fresh conversations: none sends an old conversation ID. Existing copied
histories remain historical records and do not enter the new prompts.

Product code must be committed on `v2` before launch. Record the actual launch
commit and file hashes; keep code fixed during the run. Record the unchanged `.env`
hash without its contents. Reuse the previously authorized credential without
printing or altering it. This harness is prepared before launch; preparation does
not itself authorize an additional request or an automatic retry.

## Requests and runtime

Run three unchanged questions once in `single` and once in `planned` mode through
the production HTTP/SSE endpoint. Preserve baseline order: dense single/planned,
state totals planned/single, grouped and blank cells single/planned. Use
concurrency one, port 8786, a 240-second HTTP client timeout, a 180-second provider
timeout, zero provider retries and no automatic reruns.

Keep GPT-4.1, `text-embedding-3-small`, K=5, hybrid retrieval, enabled BGE reranking,
the 4,096-token evidence budget and the baseline planned-search limits. Validate
safe runtime settings against the baseline before launch. Record actual model
revisions, device, dependencies, startup loading, exact inputs and all provider
outputs/usage. The application now uses compact table evidence and corrected
quoted-filename scope handling. Generated plans, rankings and evidence may change;
preserve and disclose those changes rather than forcing the baseline trajectories.

## Review, gates and measurement

There are 24 requested-point instances. Independently review all six answers
against the same original-page gold, actual supplied evidence and citations, then
reconcile with a second Codex reviewer. No paid judge is used. Preserve all
disagreements and failures. A correct blank observation requires the actual row,
empty positions, full grouped headers and page; a blank is never numeric zero.
All original questions are answerable. Do not substitute context-faithful
uncertainty for reference completeness.

Use the unchanged baseline gates: six complete responses; all requested points
correct and complete; all factual groups supported and individually cited; correct
row/group/blank distinctions; no fabricated counts or incorrect full refusals;
and answer/source/retrieval parity with saved history. Preserve raw source equality
and also compare shared fields because saved sources add `file_deleted: false`.

Report before/after per question and mode, separating retrieval candidates,
reranking and final supplied evidence. The identical copied index and annotations
support a matched scoped comparison. A single sample per question/mode and
generative variability limit causal conclusions; these are development cases,
not a held-out quality benchmark. Passing does not establish overall v2 acceptance
or authorize merging.

Follow the [measurement policy](../../measurement-policy.md) and retain all 20
metrics, explicitly marking missing or inapplicable values. Report first nonempty
answer delta and complete-stream latency separately, stage timings, sample counts,
means/percentiles, token usage, reliability and sequential throughput. Separate
generated answers from programmatic refusals. Billing is unavailable unless
reported by the provider; local copy duration is not ingestion or answer latency.
Keep all attempts, provider payloads, SSE events, rankings, evidence, exclusions,
assessments and saved histories append-only in this new directory.

## Launch commands

The index copy is an offline preparation step. After root confirms implementation
is committed and grants the launch go-ahead, run `prepare.py`, `start_server.py`,
`run.py` and `stop_server.py` in that order through `record_check.py`. The recorder
accepts `scope name command...`; use `offline` for preparation and local validation,
and `live` for server/request/shutdown lifecycle records. Use a unique record name
for every attempt. Do not silently repeat a failed answer request.
