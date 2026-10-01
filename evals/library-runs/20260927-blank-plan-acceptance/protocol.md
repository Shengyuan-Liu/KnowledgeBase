# Explicit blanks and complete planner coverage: matched acceptance

Repeat the unchanged three questions in both modes from the
[previous run](../20260927-table-cell-context-acceptance/README.md). Keep the exact
[questions](frozen-cases.json), [original scoring rubric](frozen-original-protocol.md),
[page gold](frozen-gold.json) and [bound facts](frozen-fact-labels.json).
The previous run completed 5/6 requests and delivered 19/24 intended points;
three unavailable semantic scores came from a planner error and two blank facts
were incorrectly omitted. Preserve every prior score and failure.

## Workload and changes

Clone the stopped baseline index under its owner lock. Verify identical PDF bytes,
extraction, child/parent chunks and embeddings; retain historical conversations.
All six requests start fresh conversations, in the original order: dense
single/planned, state totals planned/single, grouped/blank single/planned.
No upload, reparse or re-embedding. Record source-directory and .env hashes safely.
Commit product changes on v2 before launch and keep them fixed during the run.

Two product changes are under acceptance: source-metadata-pdf-v4 marks empty cells
explicitly with state=blank and directs the model to report them as blank; planner
v3 explains comparison-requirement associations and appends one unchanged resolved
question for unaddressed decomposed requirements when the existing six-query limit
permits. Original provider output and added coverage query remain separate in the
trace. Unknown IDs, exhausted slots and other invalid output still fail. No fallback
model, second planning call, new document scope or guessed evidence is introduced.

Keep the same model/settings, K=5, hybrid/BGE retrieval and 4,096-token context
budget. Use concurrency one, port 8786, provider timeout 180 seconds, client timeout
240 seconds and zero retries. Execute exactly six requests once, without automatic
reruns. Record full SDK requests/responses, actual revisions, rankings, packed
contexts, exclusions, SSE events, histories and usage. Stop the owned server after
the run. No paid judge or broad RAG benchmark is part of this subset.

## Review and gates

Use the unchanged 0/0.5/1 point rubric and factual paragraph/bullet groups. Review
all generated answers against the original page gold and their actual SDK contexts.
A blank is an observed cell content, never zero or unavailable evidence. Record
missing-information assertions separately, as in the previous rubric, and disclose
incorrect omissions alongside factual faithfulness and citation rates. A request
with no generated answer has unavailable semantic scores; its requested points
remain undelivered in the end-to-end gate. Errors are not abstentions.

One Codex reviewer performs semantic review plus a separate mechanical provenance
audit. No independent second reviewer or human review is available. Do not label
mechanical checks independent semantic review. The original multi-reviewer protocol
is preserved as a reference; this limitation is unchanged from the immediate baseline.

Functional gates: six completions, all 24 points correct/complete, all factual
groups supported and individually cited, correct row/group/blank distinctions,
no fabricated counts or incorrect full refusals, and saved-history parity.
Inspect planned assessment references and any added coverage query separately.
Passing this development subset does not establish general v2 quality or authorize
user acceptance or merging.

Follow the [measurement policy](../../measurement-policy.md). Keep all 20 metrics,
with explicit unavailable/not-applicable fields, exact evidence and all failed
attempts. Report completed-only semantic quality separately from all-intended
point delivery. Keep first answer delta, complete response and stage timings
separate; include sample counts, means, percentiles and provider usage. Billing
without a statement is unavailable. Sequential throughput is not load capacity.
The two changes and generative variability limit causal attribution; before/after
is a matched development comparison, not held-out evidence.
