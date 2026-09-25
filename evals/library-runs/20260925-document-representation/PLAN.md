# Multi-document representation correction

The initial document-scope feature passes the eight retained service questions
and two clarifications but fails the new FAQ comparison. Both files are eligible,
yet all five selected children come from admissions. Its answer then names the
wrong FAQ. Preserve the [failed run](../20260925-document-scope/README.md).

The completed correction uses a per-file vector candidate window for explicit
multi-file scopes, then prioritizes the best available hit per requested file
before additional same-file hits. Apply the same selection after optional reranking
and before its bounded input window. Scores remain unchanged. Global top-K and
packing limits remain; budgets do not magically guarantee every requested fact.
Unscoped retrieval retains the previous behavior. Scoped excerpts now carry their
resolved document identity labels in budgeted source metadata and saved snapshots.
The answer prompt and default model/settings are unchanged.

Repeat the exact 11 frozen cases, corpus and v2 annotations from the initial run,
once per case after offline regression checks. Do not rewrite earlier annotations,
answers or judgments. Compare every question with the initial run, retaining its
10/11 result and 50% comparison coverage. Source spans are stable relevance units;
rankings also retain the child-overlap proxy definition with nonexhaustive labels.

Copy the prior closed isolated index to a new run-specific directory, verify source
hashes and unchanged child/parent snapshots, and query the copy. Do not mutate the
baseline index or reingest its 17 files. No ingestion/model-loading measurement is
claimed for this pass. Historical ingestion remains 8.765 seconds in the prior run.
Up to nine query embeddings and nine answer-generation calls, zero paid judges,
zero retries, sequential, timeout 60 seconds, no warmup. Two scope clarifications
make neither query-embedding nor generation calls. Record the full query/service
pipeline, events, candidates, exclusions, metadata, usage and timings.

Use the exact initial [quality and operational gates](../20260925-document-scope/PLAN.md):
all 11 question-aligned cases, full gold-span coverage on seven answerable cases,
all claims and associated citations supported, >=80% citation coverage and a citation
per factual answer, correct personal/error abstention and scope clarification,
English text, correct document attribution, valid IDs. Service mean <=10 s/P95 <=20 s,
first nonempty service delta P95 <=10 s, input <=12000 tokens. Report generation and
service timings separately, plus executed stage timings. Do not include skipped
stages as zero-duration measurements. Record mean/median P50/nearest-rank P95 and N.

Review every output against exact source quotes/offsets; Codex is the implementer,
not an independent human. Separate default-path acceptance from general reliability
or opt-in experimental model/chunking settings. Complete metric inventory, billed
cost unavailable unless returned, no HTTP/load-capacity claims. One pass only;
record remaining failures rather than retuning prompts/models to obtain a pass.
Even a passing result does not authorize a merge.
