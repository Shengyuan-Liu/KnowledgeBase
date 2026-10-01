# Repair generic document scope and invalid optional searches

This change fixes the two deterministic failures found in the
[first-use PDF acceptance](../../library-runs/20261001-new-pdf-acceptance/README.md).
It does not rerun that acceptance or replace its failed answers. Development stays
on `v2`; the baseline is `2e82744`.

## Behavior

Unquoted source clauses containing only generic descriptor words, such as
`In the relevant document, ...`, no longer become filename restrictions. Retrieval
uses the existing selected/allowed file boundary. Quoted identities, explicit
filenames, ambiguous names and missing-file errors retain their existing handling.
A generic clause does not enable a search outside selected files.

Assessment still validates every required answer point and its source references.
Invalid optional supplementary queries are rejected individually, with their
unaltered proposal and validation reason retained under `rejected_queries` in
the assessment snapshot. Valid supported/missing judgments and valid sibling
queries survive. The controller can finish with the supported evidence and gap
instructions when no eligible search remains, instead of losing the whole answer.

All existing query provenance checks remain: only unresolved requirements may be
searched, a source-derived target must occur in each selected current passage,
and a reformulation cannot contain unbound references or a target placeholder.
Invalid mandatory assessments and malformed structured responses still fail.
No model response is rewritten, and no repair call, retry or guessed target is
introduced. Rejected proposals are not added to generation instructions or run.

## Verification and matched replay

The [recorded regression fixture](../../../tests/fixtures/new_pdf_scope_failures.json)
is extracted from unchanged acceptance artifacts and includes their SHA-256 hashes,
the exact four financial queries, the restricted assessment output and its complete
canonical evidence catalog. [comparison.json](comparison.json) replays identical
inputs through the baseline and changed code without a provider call:

| Frozen input | Before | After |
| --- | --- | --- |
| Four financial query scopes | 0/4 resolved; generic phrase treated as filename | 4/4 resolve to the original selected NVIDIA file |
| Restricted assessment | Unbound optional query raises and discards the result | Supported bridge and missing recipe retained; one proposal rejected with reason |
| Four other recorded provider assessments | Valid | Identical normalized requirements and accepted queries |

This compares local scope/validation behavior, not new model quality. Financial
retrieval rankings, supplied evidence, all four income amounts and units still need
a future matched live acceptance. No new retrieval/answer score, latency improvement
or successful true dependent chain is claimed. The original corpus, questions,
annotations, model outputs and historical failures remain unchanged.

The final scoped suite passes **185 tests**, covering source selection through
SQLite/Chroma, independent/dependent retrieval, PDF passage provenance, sufficiency,
planning, ordinary/streaming API delivery and saved history. New API tests confirm
one assessment, no rejected-query execution, unchanged explicit scope and persisted
rejection reasons. Provider responses/vectors are mocked; these tests do not establish
semantic answer quality. Existing target/provenance rejection tests were updated to
assert rejected proposals rather than entire-request errors; mandatory-invalid
assessment tests continue to require errors without history.

## Retained check attempts

| Record | Result |
| --- | --- |
| [Before-change regressions](regressions-before.json) | 8 expected failures, 21 passes; original bugs reproduced |
| [Initial scoped suite](scoped-tests.json) | 184 passes, 1 failure from an existing stale prompt-version assertion |
| [Recorded replay](recorded-replay.json) | 2 comparison groups pass; zero provider calls |
| [Final scoped suite](scoped-tests-final.json) | 185 passes; no failures or skips |

The stale assertion expected `evidence-sufficiency-v5`, although baseline production
already records `v6`. Its assertion now matches the existing runtime; no model prompt
or version changed in this repair. Both scoped runs retain the existing Starlette
`BlockingPortal` deprecation warning. No dependency upgrade is included.

Every command record contains the full 20-metric inventory, command, baseline commit,
working-file hashes, wall duration, pass/fail/skip counts and raw output. Live ranking,
answer quality, provider cost and production latency are `not_applicable` to these
offline checks; missing metrics are not filled with synthetic zeros. Test durations
are not application latency. Product changes are limited to scope parsing, assessment
validation and controller recording; no index migration or reingestion is needed.
The test fixture and run artifacts are analysis inputs, not library content.

User acceptance and a feature-specific merge decision remain separate. The prior
six-case acceptance remains 4/6 until a new live run establishes a different result.
