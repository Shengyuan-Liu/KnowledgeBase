# Markdown RAG Live Acceptance

Result: the targeted Markdown workflow passed on September 22, 2026. This is
functional development acceptance with direct Codex review of saved answers and
cited evidence, not independent human approval, held-out accuracy, or evidence
that structural chunking outperforms the MVP. Feature acceptance and merging
remain the user's decision.

## Configuration and Inputs

- Production application at commit `06b43df`, with an uncommitted acceptance harness
  and live-test configuration fix recorded alongside this report. Application code
  was not changed during acceptance.
- Real `gpt-4.1` answers/resolution and `text-embedding-3-small` embeddings, using
  the existing ignored `.env` credentials.
- Structural chunks, 512-token limit, `cl100k_base`, no overlap, vector top-k 5.
- Fresh storage: `data/live-browser/20260922T222123209Z-8d828f17`. No existing
  user library or `.env` was changed. The test server was stopped after verification.
- Three frozen Markdown documents from the repository's DeepSeek corpus:
  `guides/chat_prefix_completion.md`, `guides/kv_cache.md`, and
  `quick_start/error_codes.md`, plus one synthetic TXT garden note as a distractor.
  Source text, repository paths, and SHA-256 hashes are in [acceptance.json](acceptance.json).
  These are frozen-source tests, not a verification of today's external API documentation.

## Results

| Case | Expected behavior | Observed |
| --- | --- | --- |
| Prefix configuration | Retrieve list; identify assistant role, prefix flag, and beta URL | All three facts supported by cited source 2 |
| Code follow-up | Resolve "that guide" and retrieve exact stop parameter | Correct resolved query and code value; cited sources 1 and 4 |
| Cache rule | Preserve persisted, fully matching prefix-unit condition | Condition retained, supported by sources 1, 3, and 4 |
| Cache usage fields | Return both exact identifiers and meanings | Correct; supporting list was retrieved at rank 5 |
| Error table | Explain HTTP 429 cause and remedy from its row | Cause and pacing recommendation matched cited table |
| Missing personal balance | Abstain without inventing account data | Explicitly reported insufficient information |
| After source deletion | Exclude removed document and avoid answering from old history | Deleted source excluded; answer abstained |

Seven completed questions satisfied their stated criteria in
[reviews.jsonl](reviews.jsonl). Five answerable cases retrieved all nine annotated
literal evidence snippets. These checks are targeted coverage, not corpus-wide
recall. All citation IDs were valid; each substantive answer was separately checked
against its actual cited excerpts. The seven questions and complete answers,
resolved queries, distances, sources, and case timings are retained in
[answers.jsonl](answers.jsonl).

The browser workflow also verified:

- All four uploads reached Ready with real embeddings; 32 structural chunks were created.
- Original documents, source hashes, block associations, exact chunk slices, and
  structural metadata survived persistence. Independently recomputed token counts
  matched all 32 chunks and respected the configured limit. Heading, paragraph,
  list, code, and table block types were present.
- Clicking citations displayed original code/table markup. Refresh restored both
  completed turns of the follow-up conversation.
- Stopping an active streamed answer retained no unfinished turn in saved history;
  a reload removed the interrupted local answer.
- Deleting the prefix guide removed its source, chunks, structural metadata, and
  all five corresponding vectors. Its old evidence remained available with the
  deleted-source label. The remaining 27 vectors matched 27 stored chunks.
- A fresh production server process reopened the same directory. All three remaining
  files were Ready, and all six messages of the checked conversation matched the
  saved pre-restart response exactly, including deleted-source flags.
- No browser page errors were recorded. The Playwright scenario passed in 21.6 seconds
  (23.8 seconds including startup). Build and TypeScript checks passed.

Single-run upload observations ranged from 289 to 815 ms; completed-question
observations ranged from 1,802 to 2,821 ms, measured by browser completion checks.
These are not repeated latency estimates. Provider token usage and monetary cost
are unavailable through the application, so no cost or token totals are claimed.

## Evidence and Limits

- [Run settings and checks](acceptance.json)
- [Before-deletion storage snapshot](storage-before-deletion.json) and
  [after-deletion snapshot](storage-after-deletion.json)
- [Independent storage and vector audit](storage-audit.json)
- [Fresh-process restart check](restart-check.json)
- [Conversation after deletion](conversation-after-deletion.json)
- [Code evidence screenshot](markdown-code-evidence.png),
  [table evidence screenshot](markdown-table-evidence.png), and
  [deleted-source screenshot](deleted-markdown-evidence.png)

The UI displays exact Markdown source as plain text: fenced code, pipe tables,
and embedded `<br>` remain literal. Syntax highlighting, rendered tables, and
heading navigation are not part of this acceptance. Screenshots were reviewed at
1440 by 900; this run does not add live mobile coverage.

The five answerable cases are development probes selected from three documents.
This small sample cannot establish general answer accuracy or compare chunking
strategies. The cache-fields answer depended on the fifth retrieved result, and
some other retrieved chunks were short headings. Missing-information answers use
broad citations that do not by themselves prove an absence claim. Independent
human review and wider quality comparisons remain pending.

The [first attempt](../20260922T222038869Z-e6ab00d2/README.md) stopped after four
successful uploads because the harness inferred the wrong database directory.
Its record is retained. The fix preserves one run ID across Playwright processes;
the successful attempt used a new isolated index without automatic test retries.

## Reproduce

With `.env` configured, run from the repository root:

```sh
npm --prefix frontend run test:live:markdown
```

This makes real provider calls and writes a fresh evidence directory. The separate
TXT live workflow remains available through `npm --prefix frontend run test:live`.
The additional restart and storage audit above were run after the browser scenario;
they are saved observations, not steps included in the reproduction command.
