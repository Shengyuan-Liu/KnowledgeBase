# Single transport-timeout recovery

The completed representation correction supplied both FAQ sources and identified
the admissions page correctly. One different request, accept-unspecified-api-error,
failed mid-stream with APITimeoutError after 61.782 provider seconds. Preserve that
partial answer and failure permanently; this is not a semantic-score retry.

Make one additional service request for that case only, on a verified copy of the
same closed baseline index, using identical question, model, prompt, settings,
annotations and code. Timeout remains 60 seconds; SDK retries zero. At most one
query embedding and one generation; no ingestion or judge. Existing authorization
to use .env credentials applies. Do not retry again if this recovery fails.

Retain this as a separate attempt. Never rewrite the failed run as 11/11 first-pass
success or drop its latency/cost uncertainty. Report initial service reliability
10/11, and combined reliability including this additional request. Inspect the
complete recovery answer against source quotes and the original missing-error
rubric. No invented status code or payload, supported/cited factual extras, English.
Report service/first-delta and generation/first-delta timings separately. Missing
billing/failed-request usage remains unavailable. Recovery is not a new full-suite
acceptance or a change to production retry behavior. No merge is authorized.
