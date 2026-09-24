# Automated evaluator verification and calibration

All development work was performed on `v1`, based on `78f7e06`. This record includes
unsuccessful attempts; it is not evidence that every LLM judgment is correct.

## Offline verification

The final full suite is **508 passed, 1 skipped**, in **13.84 seconds**, with one
existing dependency deprecation warning. See `backend-6.log` and
`offline-checks-final.json` for all 14 recorded test invocations, durations, commands
and the complete metric inventory. Mocked tests are not live quality/performance.
Documentation links, formatting, source slices, budgets and secret exclusion were
checked separately. `delivery-checks.json` verifies that runtime code hashes match
the final live grading run. No frontend behavior changed, so no new browser suite
was required for this evaluator change.

## Live calibration

`calibration-1.json` through `calibration-11.json` preserve all prompts, schemas,
responses and available usage. `calibration-metrics-final.json` contains the full
metric inventory per attempt. These repeatedly use the known MSDS extra-course-type
error and are development probes, not independent calibration data.

- Initial inventories omitted answer units, paraphrased quotations, or attached
  citations that were absent from the answer line.
- `gpt-4.1-mini` and `gpt-4.1` missed the known required/elective distinction in
  inspected attempts, including an apparently valid `gpt-4.1` review.
- `gpt-5.4-mini` with medium reasoning detected the contradiction. A low-reasoning
  probe missed it, so medium reasoning remains configured.
- One request timed out at 60 seconds and another at 180 seconds. Failed-call
  billing/usage is unavailable, not zero.
- A provider-rejected `$ref` schema was reproduced once and corrected; see
  `schema-diagnostic-error.json` and `schema-diagnostic-metrics.json`.
- The final protocol uses canonical answer/source unit references, explicit
  inventory coverage and a shared definition of factual versus structural content.
  It still requires semantic inspection; successful provenance validation is not truth.

## Recorded make invocations

| Log | Outcome |
| --- | --- |
| `make-eval-1.log` | Fresh 17-document ingestion and 18 successful RAG requests. Protocol-1 grading had failures and was interrupted; in-flight provider usage can be missing. |
| `make-eval-2.log` | Reused saved RAG answers; protocol-2 grading completed, but report generation exposed absent optional categories in historical Markdown cases. Failure and recovered metrics retained. |
| `make-eval-3.log` | Reused answers; stopped protocol-3 grading after calibration exposed inconsistent handling of structural answer labels. Raw partial records retained. |
| `make-eval-4.log` | Final protocol-4 run: 15/18 current and 17/18 previous reviews valid; 15 matched pairs compared. Reports printed/saved successfully. `make` exits nonzero because three current judgments remain pending. |

The final [delivery review](../../runs/20260924T161009Z-f2950a8f-automatic/REVIEW.md)
includes the exact metrics, pending cases, and a concrete valid-looking judge false
positive. `source-audit.json` verifies all 62 supplied source slices and budgets;
`evidence-comparison.json` records every before/after evidence comparison.

The original RAG batch was executed once. Later attempts explicitly regraded saved
answers to avoid repeated answer/embedding calls. Isolated evaluation indexes and
conversations do not alter the application library. Full-set quality improvement
and independent human accuracy are not claimed.

A read-only app verification initially requested an unimplemented conversation-list
endpoint (404); it was corrected using a read-only SQLite count and the supported
conversation-by-ID endpoint. The final check found 17 unchanged file IDs, 11 saved
conversations and a successful historical read. Both attempts are recorded.
