# One bounded timeout recovery

**The one recovery request passes.** The unchanged API-error question completes
in **2.893 s**, first service answer delta **2.098 s**. Provider generation takes
**1.430 s**, first provider delta **0.640 s** (N=1; mean, median and P95 equal the
single observation). The answer correctly withholds an exact HTTP status code and
JSON body, and cites the actual `Not Supported` table status. Full text, the
required point and its supported extra claim are in [REVIEW.md](REVIEW.md).

Product hashes, question, source index, model, reasoning setting and exact provider
messages match the [failed attempt](../20260925-document-representation/README.md).
This uses one query embedding and one generation, no ingestion or judge, no SDK
retry, unchanged 60-second timeout. The resolved model is `gpt-4.1-2025-04-14`;
reported generation usage is 2234 input / 105 output tokens, and embedding usage
is 28 tokens. Billed dollars remain unavailable.

This is a separately retained attempt under [PLAN.md](PLAN.md), not a clean rerun
of all 11 questions. Combined final-code service reliability is **11/12** attempts;
the first pass remains 10/11, with its timeout and two slow completed responses.
Strict distinct-case quality reaches **10/11** when using this recovery; the
comparison answer still omits its frozen General-FAQ absence point. Full-suite
acceptance remains failed. No settings, production retries or merge changed.

[METRICS.md](METRICS.md) and [metrics.json](metrics.json) contain the complete
inventory. Gold retrieval ranking/coverage has no eligible answerable case here;
missing values do not mean zero retrieval quality. Recorded monotonic service
and batch durations are used; wall-clock timestamps span a longer unexplained interval and
are not service-performance measurements. Reviewer: Codex implementer, not an
independent human; no broad reliability conclusion from one recovery.
