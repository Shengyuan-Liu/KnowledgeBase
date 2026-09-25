# Generation Review Supplement

Effective v11 coverage is **23/24 valid reviews**, up from 22/24. No answer was
regenerated, no scoring protocol changed and no assessment was repaired.
The industry assessment completed. The credits assessment returned twice but
failed validation: claim `u28.c1` identifies source 2 by its filename, and the
judge marks that citation supported from metadata while providing an empty list
of source-text line IDs. The unchanged validator rejects this. This is a known
metadata-versus-text evidence mismatch, not evidence that the course-credit
answer is wrong. Its automatic quality result remains unavailable.

The [first supplement](../20260925-review-supplement/) contains two provider calls.
An [aborted preparation](../20260925-review-supplement-2/) incorrectly assumed the
remaining error was another timeout; its precondition failed before any provider
call. The corrected attempt here repeats only the original credits assessment,
with the original 180-second timeout. It returned the same validation problem.
No further retries were performed. All original timeouts and raw invalid outputs
remain available. `audit.json` records exact-payload checks and incremental usage.

On the **23 matched valid cases**, expected-point correctness changes from 100%
to 99.28%, faithfulness from 95.64% to 99.46%, and citation coverage from 67.20% to
81.71%. Citation support on 22 applicable pairs changes from 95.30% to 97.48%.
Appropriate abstention is 3/3, incorrect abstention 0/20. These are model
assessments on familiar development questions, not release accuracy or human
review. The previous API-setup rubric mismatch, CPT qualification regression,
and list-level citation omissions remain visible in the
[original manual review](../20260925-generation-citations/README.md).

Use `qualified-after-all.json` for combined metrics and `comparison.json` only
for its matched quality subset. Derived `judge_seconds` comparisons are invalid:
some rows time a full review and others only its last assessment. The qualified
summary marks this unavailable. Supplemental call timing and usage are separate
in `audit.json`; previous failed-call usage and actual billing remain unavailable.
Historical retrieval and generation observations are reused, not remeasured.

Codex also inspected the unchanged credits answer: several individual course and
semester bullets still omit their own citations despite later citations. The
filename-reference validation failure must not hide this real generation issue.
This manual inspection is not an independent human score and does not replace
the invalid v11 review.
