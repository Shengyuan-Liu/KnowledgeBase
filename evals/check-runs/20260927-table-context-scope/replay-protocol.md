# Frozen context and scope replay

This is an offline regression comparison, not a new live RAG acceptance run.
No provider request, retrieval query, parser invocation, index mutation, model
answer, sufficiency decision, or paid judge is part of this replay.

## Inputs and reconstruction

- Baseline product commit: `b792448`.
- Corpus, questions and annotations: the unchanged
  [dense-table acceptance run](../../library-runs/20260927-dense-table-acceptance/README.md).
- Source: one freshly parsed `background-checks.pdf`, SHA-256
  `4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407`.
- Preserve the original three questions, both modes, exact selected ranks,
  child and parent slices, PDF metadata, document labels and 4096-token budget.
- The final observed retrieval-stage result for each original request supplies
  the selected candidates. Reconstruct `pack_retrieval_candidates` inputs from
  those candidates and the original snapshot. Group parents by first selected
  child, retain retrieval provenance, attach the exact PDF evidence, and freeze
  the result once in [frozen-inputs.json](frozen-inputs.json).
- Baseline replay must reproduce packed chunks, token counts, exclusions and
  unexpanded parents exactly. Replay the original scope questions separately.
  The planned caller's not-found wording differs from direct scope resolution;
  compare its resolution fields separately and retain both messages.

The original planned queries and final ranks arose from the old context and
sufficiency cycle. They are held fixed for an isolated serialization/packing
comparison. A new live planned run may choose different queries or stop earlier.

## Scoring and preserved semantics

Use the existing source-bound fact labels. A table fact needs its target cell,
row label, complete parent and leaf header path, report period, page identity and
canonical source spans. A blank-cell fact additionally needs the complete row
and the interior zero-width cell tuple. Empty does not mean zero. Prose requires
all annotated phrases.

For each packed source, independently inspect the actual serialized context:
the excerpt must match the canonical body; pages and offsets must match; table
JSON must decode to the exact retained table metadata; every separately located
header supplement must retain its text, role and offsets. Metadata present only
in a source object cannot satisfy model-context coverage.

Report retrieval metrics only as a rescore of frozen ranks. Report packed fact
coverage separately from answer correctness, faithfulness, citation support and
abstention, which are not exercised. No old live answer score is replaced by an
offline context score.

## Scope-blocked question

Both original grouped/blank-cell requests stopped before retrieval. Their frozen
selections are empty. A repaired local scope result therefore establishes only
that the original question resolves to the ready PDF. Do not invent candidates
or claim those requests now answer correctly.

A separate direct fixture check serializes already known `child:0` and checks
the four grouped/blank-cell facts. It establishes preservation of row and column
meaning in that fixture, independently of retrieval and answer generation.

## Recording

Every invocation uses the run recorder and a unique name. Keep failed attempts
and incomplete fixes. Each comparison includes the complete 20-metric inventory,
with measured offline quantities or a concrete `not_applicable` reason. Local
packing/scope times and tokenizer counts are diagnostic values, not production
latency or provider billing. Retain code hashes, artifact hashes, exact outputs,
all source metadata, ranks, budget exclusions and per-fact checks.
