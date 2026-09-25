# Experimental semantic child chunking

Status: integrated on `v1`; opt-in, with offline verification and a
[recorded live comparison](../evals/library-runs/20260925T002400Z-semantic-acceptance/README.md).
The default remains `CHUNKING_STRATEGY=parent_child`. The experiment found two
material evidence-coverage regressions and does not justify changing the default.
Both strategies use identical bounded structural parents. User acceptance and
merge approval remain outstanding.

## Behavior

`knowledgebase/rag/semantic_chunking.py` splits each paragraph into English
sentences with source offsets, embeds those sentences, and starts a new child
when adjacent cosine similarity is strictly below the configured threshold.
There is no surrounding sentence window. Paragraph boundaries remain hard
boundaries; headings remain separate structural chunks. Lists, fenced code,
tables and other non-prose blocks keep the existing structural splitting policy.

Oversized sentences use the existing clause/word/character splits before embedding.
The final greedy packing still enforces the child token limit even if all
sentences are similar. A parent or structural boundary is never crossed.
Every child remains an exact slice of the original source, with its original
heading path, global offsets, block association and parent ID.

Sentence inputs are batched across the document. Single-unit paragraphs and
non-prose blocks need no similarity request. The final children are embedded
separately for retrieval; sentence vectors do not replace child vectors. Provider
errors use the existing failed-upload and cleanup behavior, with no silent switch
to another strategy.

## Configuration and records

```dotenv
CHUNKING_STRATEGY=semantic
SEMANTIC_SIMILARITY_THRESHOLD=0.5
SEMANTIC_BATCH_SIZE=32
```

The threshold is in [-1, 1]; batch size must be positive. These are experimental
starting values, not tuned defaults. The sentence embedding model is the same
`EMBEDDING_MODEL` used for children and questions. Parent/child budgets and
tokenizer use the existing settings. API, CLI, and both evaluation runners pass
the same resolved settings.

Use a fresh `DATA_DIR` when comparing strategies and re-upload originals. Changing
the setting only affects new uploads. This feature does not edit `.env`, reindex
the existing library, change the default strategy, or enable reranking.

The additive `document_indexes` table stores per-file indexing configuration.
Semantic records include algorithm version, exact embedding input spans, adjacent
similarities, breakpoint decisions, batch count and embedding-call duration.
Inputs can be reconstructed from the canonical source. Historical documents have
no fabricated configuration: missing records read as null. Records are written
with the source transaction and cascade on source/file deletion.

The adapter returns vectors only, so the document trace explicitly marks token
usage and billed cost unavailable. The automatic evaluation runner additionally
retains provider usage in its call log and exports per-file indexing details.
Provider model revisions are unavailable unless returned by the provider.

## Verification and comparison

The [development check record](../evals/check-runs/20260924-semantic-chunking/README.md)
links fixed-vector boundary checks, unchanged-parent comparisons, source fidelity,
budget limits, API/streaming configuration, storage and deletion checks.
Those comparisons establish implementation behavior, not embedding or RAG quality.

At feature acceptance, compare `parent_child` and `semantic` on the same frozen
corpus, questions and source-span labels, with identical parent budgets and
downstream settings. Report selected-child and packed-evidence span coverage
separately. Child-overlap ranking metrics have different units after rechunking
and must not be treated as directly comparable accuracy. Retain ingestion cost,
exact evidence, answer review and per-question regressions. Keep judge v11 frozen.

The first paired acceptance run uses 18 existing development cases and six newly
frozen questions on the same 17-document corpus. It records 48 completed answers,
source-span comparisons and unchanged parent regions. The six new cases are
Codex-authored and are not an independent release population. Semantic splitting
also keeps every paragraph as a hard child boundary, unlike the structural control;
the comparison measures that complete strategy, not the cosine threshold alone.

The [live browser workflow](../evals/browser-runs/20260925-semantic-ui-1/README.md)
also verifies source lines, saved retrieval details, follow-up, refresh and
historical evidence after deletion. Known failures and missing measurements remain
in the reports; a successful workflow does not establish answer quality.
