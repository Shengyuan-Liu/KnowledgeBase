# Period and answer-rule constraints: matched component acceptance

Repeat the exact four questions, source annotations, packed evidence, settings,
case order and scoring rubric from the
[prior failed acceptance](../20260928-answer-rules-acceptance/README.md).
The [original protocol](frozen-original-protocol.md) is retained verbatim. Product
commit 4997e75 changes planner/assessor prompts to v5, requires rules to quote the
original question, and strengthens final generation's period/column matching.

Use the copied, unchanged run.py and byte-identical cases.json. Verify resolved
settings against the baseline before launch. Keep the same final-round assessment
boundary, original question, original evidence and empty executed-query metadata.
Run each case once, sequentially, with no retries, automatic repairs or paid judge.
Do not modify product code during the run or rerun failed cases to improve scores.
Reuse the previously authorized key without changing or exposing credentials.

The baseline completes 4/4 but passes only 2/4 case gates, scores 11/13 answer points
and supports 10/12 factual claim groups. Its missing-year case falsely supports two
2016 values from a 2015 table; its factual-condition case invents an answer rule.
These failures and any new regression remain visible in the matched comparison.
Rejecting an invented rule is a request failure, not a correct answer or abstention.

Retain exact provider inputs/outputs and error attempts even if validation fails.
All-missing assessment uses the production insufficient-evidence response without
a generation call; do not count its absence of factual claims as zero faithfulness
or invent provider tokens for the skipped call. Review limitation statements
separately. The existing rubric requires appropriate abstention on the wholly
unanswerable case; a full-question insufficient-evidence response is evaluated
against both requested missing values, with its generic wording disclosed.

One Codex /root reviewer reads every plan, assessment, answer and its actual context.
No independent second or human review is available. Mechanical quote/source audits
do not establish semantic support. Keep all 20 metrics with applicable measurements
or explicit reasons; separate fixed evidence coverage from answer quality. Report
nonstreaming component stage timings and usage, not HTTP or first-delta latency.
Billed cost without billing evidence remains unavailable. No indexing, retrieval,
supplementary search, history persistence or load test is part of this subset.

This is a matched development comparison with one attempt per question and several
prompt/validation changes. It cannot isolate each change's effect or establish
statistical stability, held-out accuracy, end-to-end acceptance or merge approval.
