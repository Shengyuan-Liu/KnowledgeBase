# Independent review plan

Reviewer: Codex assistant `/root/context_review`, not a human or paid judge.
This plan is prepared before the six new answer artifacts are available. No
provider request or production change is part of this review.

Use the requested-point and factual paragraph/bullet rubric in the unchanged
[original protocol](../frozen-original-protocol.md), with the unchanged
[questions and expected facts](../frozen-cases.json) and
[source-bound labels](../frozen-fact-labels.json). The new run protocol governs
runtime and comparison differences; the original code version and fresh-ingestion
instructions in the copied protocol describe the earlier run.

For each of the six raw responses, inspect the exact answer and generation input,
the supplied and cited sources, canonical source offsets, table row/column spans,
full grouped header paths, original-page gold, and physical page. Score all 24
requested point instances for correctness, completeness and supplied-evidence
coverage independently. Valid citation IDs do not establish semantic support.

Each substantive factual paragraph or bullet is a claim group. Preserve its
exact text, cited IDs, source support and citation coverage. Repeated framing,
missing-information statements, and operational refusals are recorded separately
with a reason; they do not inflate the factual-group denominator. Review every
additional generated comparison or explanation, even when not required.

For Rentals, an observed blank requires the Alabama row, zero-width cells at
columns 16 and 17, the Rentals parent header over columns 16:18, matching leaf
headers, and physical page 1. Blank does not mean zero or no rentals. If these
structures are supplied, an answer saying the contents cannot be established is
an omission, rather than necessary uncertainty. All three original questions
are answerable; full refusals are incorrect question-level abstentions.

In planned mode, inspect every actual sufficiency call. Keep model-selected IDs,
normalized exact references and application-added table context distinct. A
selected number or row needs the correct state, grouped header and period
context; application attachment is auditable evidence, not semantic approval.

Verify saved answers and retrieval metadata exactly. Preserve raw source parity
flags and compare shared source fields separately when history adds the existing
`file_deleted: false` field. No raw flag or response is rewritten.

Do not open the new root review or receive its verdict before saving this
reviewer's independent judgments. Withhold aggregates until the root confirms
its first pass is complete. Retain disagreements and reconciliation explicitly.
Use the matched earlier six-request run for per-case comparison without changing
its scores; note remaining sampling, provider and timing limitations.
