# Parent-child rebuild of the active library

Date: 2026-09-23. The user requested parent-child chunking as the default, deletion
and re-upload of all current files, and a review of the resulting chunking quality.
Implementation branch: `v1`; this run does not authorize merging to `main`.

## Outcome

All 17 existing files were deleted through the file API and re-uploaded from
verified originals. Every file has a new ID, is Ready, and retains byte-identical
UTF-8 source. The active library is `data/`, selected by the existing `.env`.
It now contains **38 parents and 92 indexed children**, replacing 98 flat chunks.
The API was restarted at `http://127.0.0.1:8000` with `parent_child` active.
Both the built-in default and local `.env` select `parent_child`.

A consistent SQLite/Chroma backup and recovered originals are retained locally at
`data/backups/pre-parent-child-20260923T205040Z/`. Sixteen legacy TXT files had no
canonical-source row; their originals were recovered from the frozen NYU corpus
and verified against every previously stored chunk slice before deletion. The
Markdown file was recovered from its canonical SQLite source. Hashes and origins
are in [manifest.json](manifest.json); per-file delete/upload receipts are in
[rebuild.jsonl](rebuild.jsonl). The original 3 conversations, 20 messages, and 10
answer snapshots were retained. Browser acceptance subsequently added one new
conversation with one completed exchange.

## Chunking checks

[chunk-audit.json](chunk-audit.json) records all 17 files. Checks passed for:

- Every parent and child equals its exact canonical source slice.
- All non-whitespace content is covered at both levels.
- Each child belongs to exactly one parent and stays within its range and heading path.
- All children fit 512 tokens and all parents fit 1536 tokens with `cl100k_base`.
- No boundary cuts through an alphanumeric word in this library.

The Markdown file has 11 parents and 28 children. Its invocation section is one
209-token parent containing installation, environment variables, a complete code
example, and the unsupported-model note. It has nine children because headings,
list items, code blocks, and prose are distinct structural groups. Its 487-token
message-field parent preserves the full compatibility table.

The representation is useful but still has small fragments: `Tool Fields` becomes
a heading-only 4-token parent, and some headings or separators produce tiny
children. These can occupy retrieval slots without adding substantive evidence.
TXT files have no Markdown heading paths, so their parents are bounded groups of
paragraphs rather than recognized semantic sections.

See [markdown-examples.json](markdown-examples.json) for complete parent/child
examples, and [before-chunks.json](before-chunks.json) / [after-chunks.json](after-chunks.json)
for the complete stored snapshots.

## Paired real-provider check

The same 18 frozen questions were asked before and after rebuilding: 12 selected
NYU cases and 6 questions grounded in the saved Anthropic-compatible API guide.
The latter refer to the frozen guide, not independently verified current provider
behavior. Two cases require abstention. Questions were frozen before either run.

Both runs used `gpt-4.1`, `text-embedding-3-small`, top-k 5, and a 4096-token numbered
evidence budget. Each question was independent, without conversation history.
Three requests ran concurrently. No external judge model was used. Codex reviewed
answers against expected points and recorded source evidence; these are development
review results, not independent human grades or held-out accuracy.

| Measure | Existing flat library | Rebuilt parent-child library |
| --- | ---: | ---: |
| Cases containing every expected answer point | 15 / 18 | 16 / 18 |
| Expected answer points present | 43 / 48 | 45 / 48 |
| Annotated character-span coverage, 16 answerable cases | 83.28% | 90.58% |
| Mean numbered evidence tokens | 1615 | 2587 |
| Mean request time, this concurrent run | 3.28 s | 3.06 s |
| Invented requested facts in the 2 unanswerable cases | 0 | 0 |
| Invalid citation IDs | 0 | 0 |

**Expected-point completeness is not an overall correctness score.** In particular,
the after answer about the Industry Concentration adds an unsupported alternative
("or comparable industry experience") despite covering the expected mandatory
internship points. Both personal-schedule answers add advice about registration
outside the supplied evidence. These issues are retained in [reviews.jsonl](reviews.jsonl).
Valid citation IDs do not prove semantic support.

This is a comparison with the user's actual former library: 16 TXT files used the
MVP character splitter, while the Markdown file used flat structural splitting.
It is not a controlled experiment isolating parent expansion alone. Parent evidence
uses about 60% more context here. Higher span coverage partly reflects longer text,
and these timings do not establish a latency improvement. Markdown gold spans cover
whole sections, so omitted blank separators can prevent perfect full-span scores
even when all requested facts are present.

## Findings worth acting on

1. **API setup improved.** Before rebuilding, the answer named the SDK but could
   not supply the environment variables or invocation method. After rebuilding,
   the highest-ranked heading child expands to the complete invocation parent;
   the answer includes `pip install anthropic`, `ANTHROPIC_BASE_URL`,
   `ANTHROPIC_API_KEY`, and `client.messages.create`. All three expected points are
   supported by the supplied parent. The six Markdown questions have complete
   expected points after rebuilding, versus five before.
2. **Degree context became more explicit.** Both answers gave 36 credits and the
   four-semester schedule. The former answer inferred the total from the plan;
   the new answer receives explicit degree requirements plus the schedule caveat.
3. **GPA still fails at retrieval.** Neither run supplies the correct general-FAQ
   passage with GPA 3.0 and 66% completed credits. The new top-five hits favor
   admissions content and referenced-link lists. Expanding their parents cannot
   recover the missing passage. The answer also overstates the absence of a FAQ
   requirement instead of limiting the claim to its retrieved evidence.
4. **CPT still fails, now visibly at packing.** The rebuilt search does find the
   admissions FAQ child saying paid internships for credit occur after year one.
   It is candidate 5. Its 1525-token parent is excluded after 3327 tokens of earlier
   context were packed, exceeding the 4096-token budget. The answer supplies the
   concentration's first-year requirement but misses the contrasting FAQ rule.
   Candidate recall succeeded; the final evidence selection failed.
5. **Small structural fragments and irrelevant context remain.** A heading-only
   `Tool Fields` parent appears among the API-tool sources. Some TXT hits are
   reference-link lists whose expanded parents consume substantial context.

The parent-child path is functioning and helps preserve complete local context,
particularly for multi-block Markdown instructions. It is not sufficient by itself
to resolve retrieval misses or prioritize evidence under a budget. The next useful
quality work is selecting better child candidates (hybrid retrieval/reranking) and
packing parents so lower-ranked but necessary evidence is not displaced. No tuning
was applied after seeing these questions, and the 4096-token setting was retained.

## Records and reproducibility

- [cases.json](cases.json): frozen questions, expected points, and original gold spans.
- [before-answers.jsonl](before-answers.jsonl), [after-answers.jsonl](after-answers.jsonl):
  full answers, source text, candidates, budget exclusions, token counts, and latency.
- [corrected-coverage.json](corrected-coverage.json): authoritative automatic coverage.
  The initial run outputs compared corpus-relative gold filenames to upload basenames,
  incorrectly scoring NYU spans as zero. Coverage was recomputed from the saved
  answers with basename normalization, without repeating model calls. Original rows
  and stage summaries are preserved for audit; their embedded coverage values are
  superseded by this corrected artifact.
- [reviews.jsonl](reviews.jsonl), [comparison.json](comparison.json): per-case Codex
  review and consolidated results. Full expected points and extra unsupported claims
  are distinguished.
- [browser-conversation.json](browser-conversation.json),
  [parent-evidence.png](parent-evidence.png): an additional real streamed answer,
  full parent evidence in the UI, and successful refresh/restoration. A first browser
  inspection hit an ambiguous locator because the same citation appears repeatedly;
  selecting the first occurrence completed inspection without a second model call.

[run_evaluation.py](run_evaluation.py) replays the frozen questions against a chosen
library with fresh output names. Stop the process owning that directory first.
This uses the existing `.env` key and incurs real provider charges:

```sh
PYTHONPATH=. uv run --locked python \
  evals/library-runs/20260923T205040Z-parent-child/run_evaluation.py \
  evals/library-runs/20260923T205040Z-parent-child repeat --data-dir data
```

Do not reuse an existing stage name. The replay runner normalizes evidence filenames
before computing coverage. Its per-run settings do not reindex an existing library.

Configuration and compatibility checks: **393 backend tests passed, 1 live-provider
unit test skipped**. The live calls above are separate from that skipped unit test.
