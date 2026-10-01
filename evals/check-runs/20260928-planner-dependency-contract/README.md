# Conditional retrieval and dependency-template contract

The latest [live acceptance](../../library-runs/20260928-planner-fact-scope-acceptance/README.md)
completed 3/4 requests and passed 2/4 case gates. The factual-condition plan used
dependent queries despite already knowing every search input; both templates
omitted `{target}`. The missing-year plan still transferred "ungrouped" to
Pre-Pawn Handgun. This offline update addresses the request contract and prompt
guidance. It does not establish recovery of either live semantic failure.

## Implementation

- `DependentQuery.query_template` now exports a `pattern` requiring the literal
  `{target}` to the provider schema. Previously the runtime-only validator was
  invisible in that schema. The existing count validator still requires exactly
  one placeholder; the presence pattern alone does not enforce uniqueness.
- Planner v7 distinguishes independent searches for conditional facts from a
  search needing an entity or term discovered in earlier evidence. A named row's
  blank cell, known column value and explicitly requested explanation can be
  queried independently. The answer still obeys the original condition.
- A concrete column example preserves "ungrouped Handgun" and "Pre-Pawn Handgun"
  separately. It also preserves both modifiers when the user explicitly names
  both columns as ungrouped. These are prompt instructions, not a semantic filter.

The [official Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas)
documents string `pattern` support. The local real-SDK mock-transport test verifies
that this constraint is serialized into the actual request. Provider acceptance
of this exact changed schema has not been exercised live in this run.
No extra provider call, retry, automatic route conversion, output repair,
assessment change, generation change or stored-data migration is introduced.

## Frozen comparison

[Preparation](preparation-1.json) copies all four exact prior questions, planner
requests and raw model outputs into [frozen-cases.json](frozen-cases.json), with
source hashes. Corpus provenance remains the same frozen November 2015 table;
no retrieval, assessment or generation occurs in this planner-only comparison.
The corrected historical note about ordinary decoded filename quotes is retained
as a source reference. There is no filename-escaping defect in this change.

The comparison uses the recorded v6 request as the before arm and the current v7
production planner with mocked output as the after arm. Both original outputs
and explicitly authored expectations are replayed. Annotations move the two
fully specified conditional queries into the initial query list and remove only
the incorrectly transferred modifier from the missing-year R2/Q2. They do not
change the question, year, facts, user rule, or evidence. They are supplied test
outputs, not a transformation performed by production code.

| Case | Original output under current code | Annotated expectation under current code |
| --- | --- | --- |
| Original answer rule | Four facts and original rule preserved | Same output |
| Paraphrased answer rule | Four facts and original rule preserved | Same output |
| Factual condition | Two targetless templates rejected by the new field pattern | Three independent queries, same three factual requirements |
| Missing year | Two facts accepted, including wrong Pre-Pawn qualifier | Two facts accepted with corrected column name and unchanged November 2016 scope |

[Comparison artifacts](comparison-1.json) retain exact old/new requests, supplied
outputs, returned plans and validation errors. The two invalid templates do not
match the new transmitted pattern. They were already rejected locally before
this change; no recovered live request is claimed. A model could still choose a
semantically wrong route with a syntactically valid placeholder. The raw column
error still passes local validation and remains an open live-verification item.

Local serialized planner input grows by 372 `cl100k_base` tokens per case: from
1,532-1,594 to 1,904-1,966, below the unchanged 8,192 cap. These are local input
estimates, not provider usage, billing or latency measurements. Requested model
(`gpt-4.1`), original/resolved question payload, 2,048 output-token cap and one-call,
zero-retry behavior are fixed. The original live resolved model was
`gpt-4.1-2025-04-14`; this run resolves no provider model.

## Verification and remaining limits

- [Focused tests](focused-1.json): 73 passed, 0 failed, 0 skipped; pytest 3.28 s.
- [Scoped tests](scoped-1.json): 222 passed, 0 failed, 0 skipped; pytest 8.07 s.
  Coverage includes planning, dependency binding, sufficiency, document scope,
  chat/API, streaming, historical records and citations. Existing three-hop tests
  retain genuine source-derived target binding. One existing Starlette/AnyIO
  deprecation warning remains.
- [Comparison check](comparison-1-check.json): eight sequential mocked planner
  replays across four frozen questions; one mocked call per replay, no retries.
- [Documentation review](documentation-1.json): content, local links, formatting,
  frozen-source integrity and complete metric inventories.

Records include base commit `e74a5d6`, changed/tracked file hashes, commands,
device, durations, counts, failure artifacts and all 20 required metric entries.
Local test runs do not load a retrieval model or exercise production queues.
Live retrieval/answer quality, evidence coverage, provider usage/cost, production
latencies, throughput and ingestion are not applicable to these mocked checks;
the recorded test durations do not substitute for them. Paid calls: zero.

Reviewer: Codex /root, direct inspection of exact plan fields and requests.
Annotations are development expectations, not independent human labels. The
prompt now uses the observed column phrase, so a future matched rerun is a
development regression check, not held-out generalization evidence. Broader
semantic reliability, bounded live follow-up and user acceptance remain open.
This change stays on v2; no merge is authorized by these checks.
