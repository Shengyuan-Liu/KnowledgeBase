# Final merged-v1 browser acceptance

One real-provider desktop Chromium workflow on the production API/static build,
with unchanged product code from merge 483a156. Two frozen synthetic fixtures:
General Lab Guide (TXT): weekdays 9 AM-6 PM, weekends 10 AM-2 PM; Lab Access Guide
(Markdown): confirmed reservation for weekends, request at least 24 hours ahead.
The exact fixtures/questions are frozen in frontend/live/release.spec.ts before
calls; references are not injected into generation. This is functional checking,
not a held-out benchmark or independent human review.

Three completed questions: scoped weekday hours; follow-up weekend hours retaining
General scope; comparison identifying Access as the explicit reservation policy
and General as not specifying one. Every factual answer must cite its supplied
excerpt; inspect exact answers, qualifications and extra claims manually. Verify
source slices/lines, both comparison documents, history and scope after refresh.
Then submit one longer scoped question and press Stop while answering. Verify no
unfinished turn persists after refresh. Cancellation may occur before first text;
do not claim a mid-token cancellation unless recorded. Finally delete both test
files through the UI, confirm all live source/chunk/index rows gone, and retain
historical evidence/diagnostics with deleted labels. An empty library disables
new submissions. Review saved screenshots and browser JavaScript errors.

Default structural parent-child, hybrid top-5, 4096-token evidence, GPT-4.1,
text-embedding-3-small, omitted reasoning, reranking off. Use isolated
DATA_DIR=data/live-browser/20260926-v1-final-ui-1, one worker, no test/SDK retries,
60-second provider timeout, and temporary caffeinate -i -s. No normal data or
.env mutation. At most two ingestion embedding calls, four query embeddings,
four generations and three follow-up resolution calls; cancellation can prevent
some calls. Actual upstream usage/counts/resolved revisions are unavailable on
this unmodified API path and must not be asserted from these upper bounds.
No judge, extra quality sampling, model changes or fixes to force a passing answer.
Retain failed attempts; a harness-only failure may be resumed in a separate record
against saved state without resubmitting completed questions.

Record code/config/fixture hashes, command/duration/counts, exact saved evidence,
rankings, budget exclusions and completed HTTP SSE bodies when readable. Capture
submit-to-visible-completion latency as UI timing, not exact first provider delta
or generation latency. Missing transport/provider metrics remain unavailable.
Retain a complete metric inventory and manual semantic observations separately.
Document known warnings and independent-validation gaps in the v1 summary.
This check does not authorize any additional merge or remote push.
