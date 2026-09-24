# Claim judge calibration

Run `make eval-calibrate` before adopting a changed judge. This exercises the
production three-stage judge on 16 fixed synthetic answers and source excerpts:
ten correct answers, five known errors, and one appropriate refusal. The examples
are derived from observed extraction/support failures, including alternatives,
restrictive qualifiers, required versus elective courses, installation instructions,
source provenance, paraphrases, nonexhaustive lists, editorial summaries and missing
personal schedules. Source lead-ins and abbreviated nested-field summaries cover
two further semantic failures observed in the saved-answer review.

[Cases and labels](cases.json) were authored by Codex and frozen before the live
comparison. They are development labels, not independent human ground truth.
The grader receives questions, expected answer points, answers and sources; the
calibration expectations and label rationales are not included in its payload.
The fixed set is deliberately small and does not establish general accuracy.

For a correct factual unit, at least one factual claim must be extracted and all
claims in that unit must be supported. A known-error unit must contain the labeled
contradicted or insufficient claim; a failed/incomplete review does not count as
detecting the error. Refusal flags are checked separately. Correct answers/refusals
must receive full expected-point credit. Claim counts can differ between protocols;
agreement uses answer units and case IDs, not positional claim IDs.

`calibration_agreement` divides passed cases by all planned cases, counting pending
reviews as failures. `correct_answer_rejection`, `known_error_miss` and
`refusal_mismatch` report separate passed, mismatched and pending counts with the
full category denominator. Known-error detection accepts either negative support
verdict; confusing `contradicted` with `insufficient` remains a classification error
in `calibration_agreement`, but is not counted as accepting a wrong answer.
Judge quality scores are retained as diagnostic model
assessments. Reliability, latency (mean/median/nearest-rank P95), actual token usage,
concurrency and throughput are recorded separately. Billed cost is unavailable;
retrieval, generation and ingestion metrics are not applicable to synthetic inputs.

Every run preserves exact prompts, strict schemas, raw responses, extracted claims,
source references, model settings, code hashes, labels and failures in a new
`evals/calibration-runs/` directory. There is no retry or answer repair. A mismatch
or pending review produces a nonzero exit status after saving and printing reports.
`make eval` continues to run the full frozen RAG benchmark with the current judge;
`make eval EVAL_ARGS="--answers-from evals/runs/<run-id>"` reuses recorded answers.

This follows the [OpenAI grader guidance](https://developers.openai.com/api/docs/guides/graders)
to evaluate a grader against labeled answers and retain discovered edge cases.
The project uses its own Responses-based runner, not the hosted Graders API.

See the [2026-09-24 delivery review](../check-runs/20260924-judge-calibration/REVIEW.md)
for all comparison limits and the remaining pending calibration judgment. Default
reasoning is `high`; this improves the observed calibration but increases evaluation
latency and usage. It does not change the RAG answer model or user-query latency.
