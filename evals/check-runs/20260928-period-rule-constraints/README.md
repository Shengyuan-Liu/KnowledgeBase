# Period matching and user-rule provenance

This update addresses the two observed failures in the
[four-case live acceptance](../../library-runs/20260928-answer-rules-acceptance/README.md):
an invented answering rule and November 2015 values incorrectly used for a November
2016 question. No live requests are made in this implementation check. The prior
failed acceptance remains unchanged and is not superseded by offline test results.

## Changes and boundaries

- Planner v5 requires `answer_rules` to quote exact contiguous text from the
  original user question. The client rejects any rule absent from that question
  before retrieval. It does not delete the rule, repair output or retry the call.
  The copied example that prompted the observed invention is removed. A model
  that still invents or paraphrases a rule will now fail the request; a correct
  answer is not guaranteed after rejection. Exact text provenance does not prove
  that the quoted text is semantically an answering instruction.
- Assessment v5 explicitly checks the requested document, entity, period, measure
  and complete column group together against source text. Other-period values
  alone must be missing, with the period mismatch stated in the gap. Period/header
  passages must accompany dated-value support. A multi-period requirement may
  still be partial when one requested period is actually supplied.
- Generation instructions independently require the requested period and column
  path, even when the assessment incorrectly says supported. Planner instructions
  also forbid transferring one column's qualifier to another column.

Period matching and column interpretation remain semantic model instructions.
There is no general year regex, date inference engine, semantic status rewrite or
additional model call. Historical records retain their original outputs.

## Frozen comparison

[Comparison](comparison-1/summary.json) binds the original questions, evidence,
protocol and observed model outputs by SHA-256. The historical implementation is
`5447c29`; this change starts from `9a6e65c`, with current file hashes in each check
record. Reviewer: Codex /root, no independent second or human review.

| Controlled input | Historical or unchanged behavior | Current behavior |
| --- | --- | --- |
| Exact invented-rule planner output | Accepted in the live run | Rejected after one mocked call; no repair or retry |
| Three observed legitimate user rules | Accepted | Accepted verbatim, with all factual requirements preserved |
| Exact wrong-year assessment output | Both 2016 points supported, wrong answer | Still passes provenance validation; frozen wrong answer preserved |
| Reviewer-annotated missing assessment | Not a historical model result | Both points missing; insufficient-evidence answer without generation |

The period annotation changes only the two statuses, gaps and references. It
does not change the question, plan, evidence text or catalog. Context hashes are
identical. The final-round fixture stops at `round_limit` on missing evidence;
supplementary retrieval is not executed. Requests preserve the 2016 question and
the source's `[p2] November - 2015` header, and tests verify that both the assessor
and generator receive the new period instructions.

These checks establish payload and control-flow behavior, not model compliance.
In particular, the old semantic error is intentionally still reproducible when
the provider output is held fixed. The annotated result must not be reported as
an observed answer-quality or abstention improvement. No source evidence exists
for the requested 2016 values in this fixture; a retrieval coverage score is not
invented for those absent facts.

## Checks

- [Focused regression](focused-1.json): 105 passed, 0 failed, 0 skipped;
  pytest duration 4.24 seconds.
- [Scoped regression](scoped-1.json): 290 passed, 0 failed, 0 skipped;
  pytest duration 9.19 seconds. Covers planner/sufficiency, PDF tables, retrieval,
  document scope, chat, streaming and citations. One existing Starlette/AnyIO
  deprecation warning remains.
- [Controlled comparison command](comparison-1-check.json): completed without
  provider calls. Exact current requests, contexts and assessments are retained
  in the two comparison artifacts.
- [Documentation review](documentation-1.json): English content, links, formatting
  and comparison boundaries checked without additional model calls.

Every command record retains exact invocation, base commit, file hashes, device,
duration, pass/fail/skip/error counts and the complete 20-metric inventory.
Live answer quality, provider cost, production latency, throughput and ingestion
are not applicable to these mocked checks. Evidence text equality is a structural
observation, not a quality score. Local durations are not production timings.
Use new record/directory names when rerunning; artifacts are append-only.

Next acceptance must use the same frozen four questions and evidence to test
actual model behavior, including the risk of rule-validation errors. Current
prompts have not received live acceptance. No merge is part of this change.
