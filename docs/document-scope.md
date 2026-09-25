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

The recognized prefixes are `According to`, `In`, `From`, `Using` and `Compare`.
A clause must contain a document descriptor (FAQ, guide, document, file or page),
a `.txt`/`.md` filename, or a quoted name. Quote names containing commas, colons
or `and`, using double quotes or backticks. Matching is case-insensitive.
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
status and clarification. `scope_seconds` measures identity lookup/resolution
inside total retrieval time, not an extra duration to add to it. Source IDs remain
contiguous in packed evidence order. Existing snapshots retain scope, excerpts,
locations and citations after refresh and file deletion. The UI's Debug details
shows the recorded document names; historical records without scope are not inferred.

Multiple selected files are eligible for ranking; selection alone does not promise
that every file will have a hit in the final top-K/budget. The answer must acknowledge
missing evidence. Document scope prevents cross-file retrieval for recognized
restrictions; it does not guarantee model faithfulness, completeness or language.

[Check records](../evals/check-runs/20260925-document-scope/README.md) cover source
matching, vector/BM25 filtering, API/streaming/history parity and browser workflows.
