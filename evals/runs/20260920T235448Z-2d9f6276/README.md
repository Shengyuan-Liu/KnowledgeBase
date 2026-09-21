# Paired chunk-size control: 256 characters

This is the control in the [256-versus-512 experiment](../../analyses/2026-09-20-chunk-size-256-vs-512.md).
It uses the 25-case development set and 16 frozen TXT documents, not a held-out test.

- [Graded report](reports/20260920T235745Z-c2674e8d.md)
- [Machine-readable graded snapshot](reports/20260920T235745Z-c2674e8d.json)
- [Run settings and code provenance](run.json)
- [Original answers and retrieved sources](answers.jsonl)
- [Single-round LLM reviews, exact prompts and raw responses](reviews.jsonl)
- [Frozen cases and reference evidence](cases.json)
- [Frozen corpus manifest](corpus.json)

Generation used commit `5279334443d3025983b73f69db241eec635d7a06`,
`gpt-4.1-nano`, `text-embedding-3-small`, 256-character chunks, overlap 64,
and top-k 5. Each run used a fresh isolated index. The paired runs have identical
implementation/lockfile and input hashes. The control captured a clean checkout;
the candidate and grading sessions captured untracked experiment outputs, with
no tracked diff or implementation changes.

All 25 answers succeeded. One grading round with `gpt-4.1-mini`, reviewer
`gpt-4.1-mini-v1`, produced 25 schema-valid reviews and **14/25 strict passes**.
Recorded annotated character recall is **53.35%**
and full evidence recall **44.17%**, each averaged over
20 answerable questions. Original ungraded reports remain as earlier snapshots;
the links above select the graded snapshot.

The [paired analysis](../../analyses/2026-09-20-chunk-size-256-vs-512.md) documents
incorrect judge decisions in both arms. These are raw LLM judgments, not human
ratings or verified accuracy. No review retries, manual score substitutions, or
application default changes were made. This is one observation per setting;
provider variation, increased context size, and changed chunk boundaries limit
causal interpretation. Token usage and monetary cost were not recorded.

Markdown report line endings were normalized for display. Exact source and answer
whitespace remains in the unmodified JSON/JSONL records and report snapshots.
