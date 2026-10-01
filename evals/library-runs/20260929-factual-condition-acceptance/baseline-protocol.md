# Dependency contract: matched live component acceptance

Freeze product commit bb4bc94 and compare against the immediately preceding
[live run](../20260928-planner-fact-scope-acceptance/README.md). Preserve its
[protocol](baseline-protocol.md) and the original [rubric](frozen-original-protocol.md).
Use byte-identical cases, runner, evidence and runtime settings. The only product
changes are planner v7 instructions and the dependency-template presence pattern;
assessment remains v5 and generation remains unchanged.

Run each of the same four questions once, sequentially, with the already authorized
credential and requested model gpt-4.1. Record the actual resolved revision.
Zero provider retries, no automatic repair, no paid judge, at most 12 SDK calls.
Retain any provider or application errors and do not rerun for a better outcome.
Freeze this protocol before any paid call; do not modify product code during the run.

The immediate baseline completed 3/4 requests, passed 2/4 case gates and delivered
10/13 intended points. Its completed-only answer scores were 10/10, with three
unavailable semantic points from the planner error. Keep that denominator
distinction when comparing outcomes; a failed request is not a correct abstention.

Check these same gates without changing the rubric:

1. Original answer rule: preserve four cell facts, actual user rule, document,
   entity, period and column paths; correctly answer with individual citations.
2. Paraphrased answer rule: retain the same behavior without an invented rule or
   duplicate evidence-sufficiency requirement.
3. Factual condition: retain blank/value/explanation as three factual points and
   no answer rule. All search inputs are known, so queries should be independent,
   with no dependency placeholders invented for known entities. Support the two
   available facts and disclose the unavailable explanation.
4. Missing year: retain two November 2016 values, separate the actual answering
   rule, preserve ungrouped Handgun and Pre-Pawn Handgun as distinct column paths,
   and withhold unavailable values. The existing rubric accepts a generic local
   full-question refusal for both absent values if all-missing is reached.

The model receives the frozen packed November 2015 PDF table and original page
annotations, with no new retrieval. Invoke production planning, final-round
assessment (round_index=3, empty executed-query metadata) and bounded generation.
No upload, embedding, search, reranking, supplementary retrieval, history, HTTP,
streaming or load test is performed. Proposed queries are not executed searches.

One Codex /root reviewer reads every plan, query, assessment, answer and supplied
context against the fixed source facts. Keep expected-point, factual-claim,
citation and absence-statement judgments. No independent second or human review
is available. Structured judgments and valid provenance are not semantic truth.

Retain all 20 measurement-policy metrics with values or explicit scope reasons;
SDK inputs/outputs, errors, usage, resolved models, settings, hashes and device.
Measure component totals and affected-stage timing separately (n/mean/P50/P95,
linear interpolation), with provider queues included but not isolated. No local
model loading occurs. Component duration is not HTTP latency or time to first
answer delta; billed cost is unavailable without billing evidence. Do not count
skipped generation as a paid call or invent its usage.

This is a development regression comparison on reused cases whose wording now
appears in prompt examples. It does not establish held-out generalization,
repeatability, isolated causality, full-loop acceptance or merge authorization.
Preserve both improvements and regressions, including the previous failed run.
