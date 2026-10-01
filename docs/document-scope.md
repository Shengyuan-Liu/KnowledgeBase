# Document-scoped answers

A question naming the general FAQ must not silently borrow an admissions-only
statement. Document scope restricts eligible files **before** vector search and
BM25 statistics/ranking. Reranking, parent expansion and evidence packing only see
hits from those files. The same scope applies to complete and streaming answers.

## Asking about a document

Use an explicit leading source clause, followed by a comma or colon:

- `According to the general FAQ, how are scholarship applicants considered?`
- `In the saved DeepSeek Anthropic guide, what happens to anthropic-version?`
- `According to the general FAQ and admissions FAQ, which page describes a separate application?`
- `Compare "general-faq.txt" and "admissions-faq.txt": what differs?`
- `In "background-checks.pdf" for November 2015, report Alabama's Totals value.`

The recognized prefixes are `According to`, `In`, `From`, `Using` and `Compare`.
A clause must contain a document descriptor (FAQ, guide, document, file or page),
a `.txt`/`.md`/`.pdf` filename, or a quoted name. Quote names containing commas, colons
or `and`, using double quotes or backticks. Matching is case-insensitive.
For a quoted reference, the closing quote ends the document identity. A following
qualifier such as `for November 2015` remains in the original question supplied to
the answer model; it is not appended to the filename. An unquoted `and` still
separates document references.
This is deliberately bounded syntax, **not arbitrary natural-language document
recognition**. For example, `What does my guide say?` does not establish a scope.
Queries such as `In fall 2026, how many credits?` remain ordinary library queries.

Exact filename/identity-label matches take precedence; otherwise all meaningful
reference words must occur in the file's identity labels. Labels use the filename
stem, the opening `Title:` line or Markdown H1, and an opening `Source:` URL
hostname. Descriptor words such as `saved`, `the` and `guide` are ignored in the
word match. There are no corpus-specific aliases, fuzzy similarity guesses,
body-text matches or additional provider calls. Legacy files can use filenames.

Every named document must resolve uniquely. Ambiguous or missing references return
an English clarification with **no retrieval or answer-generation call**, not an
answer assembled from the other files. A scope with insufficient evidence stays
within that scope and uses the existing evidence-limitation behavior. Matching a
name does not establish that the document contains the requested answer.

Planned mode preserves the initial missing or ambiguous reference, candidate
matches and clarification before search. It does not re-resolve that failure
against an empty file catalog or replace it with a generic missing-file message.
The planner is also skipped for an unresolved scope. Complete answers, streaming
answers and saved history retain the same scope and clarification.

## Explicit API selection

Both `POST /api/chat` and `POST /api/chat/stream` accept optional, nonempty
`file_ids`, using ready IDs from `GET /api/files`:

```json
{"question": "How are applicants considered?", "file_ids": ["<ready-file-id>"]}
```

The streaming request also needs `request_id`. Explicit IDs narrow the name-matching
catalog first, so they can disambiguate duplicate filenames. A missing/not-ready
ID or a conflicting named document returns a clarification, without falling back
to other files. Omit `file_ids` for normal library behavior; an empty list is a
request-validation error. The current UI accepts natural source clauses; explicit
ID selection is an API capability, not a new UI picker.

Scope is per request, not a sticky conversation setting. The existing conversation
resolver is instructed to preserve source clauses when a follow-up refers to the
same document. Original explicit source clauses take priority over its rewrite;
other reference resolution still depends on the resolver. An explicit API caller
should resend `file_ids` for each constrained turn.

## Implementation and records

`rag/scope.py` is a pure identity helper, not a new agent or database table.
`retrieve_evidence` resolves the scope using ready-file metadata, then supplies
the restricted IDs to both search paths. Canonical title text is read in one batch
only for named requests; no index rebuild or schema migration is needed.

`retrieval.document_scope` records references, resolved IDs or ambiguous candidates,
status and clarification. Where recorded, `scope_seconds` measures identity lookup/resolution
inside total retrieval time, not an extra duration to add to it. Source IDs remain
contiguous in packed evidence order. Existing snapshots retain scope, excerpts,
locations and citations after refresh and file deletion. The UI's Debug details
shows the recorded document names; historical records without scope are not inferred.

For explicit multi-file scopes, vector candidates are fetched per file. Candidate
selection reserves the best available hit from each file before additional hits
from the same file; the bounded reranker input and final selection use this policy.
RRF/reranker scores and original ranks are not rewritten. The final selected-child
list can therefore include a result outside the ordinary global top-K. Both the
ranking and actual selection remain in diagnostics.

Scoped excerpts carry `document_labels` (filename identity, opening title and source
hostname) in context metadata and saved sources, including when the excerpt itself
does not contain the document title. Metadata counts toward the unchanged token
budget; scoped context uses `source-metadata-v2`. Unscoped context retains v1.

Top-K and context limits still apply: selection alone does not promise that every
file will have a passage in the final budget, especially with more files than K. The answer must acknowledge
missing evidence. Document scope prevents cross-file retrieval for recognized
restrictions; it does not guarantee model faithfulness, completeness or language.

[Check records](../evals/check-runs/20260925-document-scope/README.md) cover source
matching, vector/BM25 filtering, API/streaming/history parity and browser workflows.

The [quoted-reference regression checks](../evals/check-runs/20260927-table-context-scope/README.md)
cover trailing date qualifiers, explicit file restrictions and ambiguous names,
plus preservation of planned clarifications in both API modes and history. These
are offline checks with mocked providers, not live answer-quality measurements.

The [initial live acceptance](../evals/library-runs/20260925-document-scope/README.md)
retains the multi-document candidate-starvation failure that motivated this correction.

The [final correction report](../evals/library-runs/20260925-document-representation/README.md)
confirms both FAQ sources and correct attribution, with full annotated comparison
coverage. Strict acceptance still records a missing explicit contrast point,
slow generations and one stream timeout. The [bounded recovery](../evals/library-runs/20260925-scope-timeout-recovery/README.md)
passes that failed request separately; it does not erase first-pass reliability
or authorize a merge.


The subsequent [awake-host acceptance](../evals/library-runs/20260926-comparison-awake/README.md)
passes all 11 unchanged strict cases, including both comparison points, and the
original latency gates. Host power logs explain a confound in the previous timing
sample; old failures remain unchanged. The generation format now explicitly
preserves one item per compared document. The new report retains a non-fatal
stream-finalizer warning and wording limitations; success supports the default
path's merge recommendation, subject to explicit user approval.
