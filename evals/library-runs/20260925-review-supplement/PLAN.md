# Missing assessment supplement

The user authorized completing the two timed-out judgments. Reuse the exact
answers, inventories, audits, assessment payloads and v11 schema for `msds-credits`
and `msds-industry` from the generation-citation run. Submit only their final
assessment calls, once each, at the recorded model and high reasoning effort,
180-second timeout, SDK retries disabled, concurrency two. No answer regeneration,
retrieval, protocol changes or score repair. Keep previous timeouts intact.

`supplemental-*.jsonl` contains only new attempts. `answers.jsonl`, `freeze.json`,
`reviews.jsonl` and `calls.jsonl` are derived comparison views: historical bytes and
successful reviews are reused, effective reviews replace the two missing results,
and calls include all old attempts plus new attempts. Incremental provider usage
must be taken from supplemental calls only. Combined metric files include the
historical generation and judgment workload and remain a single-pass assessment,
not new retrieval or load testing. Missing billing and failed-call usage remain
unavailable. A successful retry does not erase the initial failure rate.

Preflight: two mocked checks confirm exact payload/schema replay, inventory reuse,
and original-error preservation. First invocation used an unsuitable pytest entry
point and failed import collection; the corrected `python -m pytest` invocation
passed. Both records are retained under `../../check-runs/20260925-retrieval-coverage/`.
