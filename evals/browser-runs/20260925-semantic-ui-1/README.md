# Live semantic evidence workflow

One real-provider browser test passed on 2026-09-25 UTC (2026-09-24 local time),
using an isolated library and two synthetic questions. This verifies the semantic
upload and evidence UI workflow; it does not establish general answer accuracy.

## Verified behavior

- Markdown upload records `semantic` indexing and exact original source text.
- Both answers include valid citations, exact source slices, correct original
  line ranges, hybrid rankings, local reranker records and query-embedding timing.
- The follow-up resolves the lab context. Refresh restores both completed answers
  and the same saved retrieval diagnostics.
- Document deletion removes file/source/indexing/parent/child records. After
  refresh, historical excerpts, line ranges and diagnostics remain available,
  and the UI labels the source as deleted.
- No browser JavaScript errors occurred. Codex visually reviewed both screenshots:
  [restored evidence](restored-evidence.png) and
  [deleted-source history](deleted-evidence.png).

## Answer inspection

Reviewer: Codex, against the exact synthetic fixture and saved supplied excerpts
in [acceptance.json](acceptance.json); not independent human grading. Expected
answers were defined in the test before generation. No LLM judge was called for
this workflow. These qualitative observations supplement the runner's explicitly
unavailable formal quality metrics; they are not benchmark scores.

| Question | Actual answer | Evidence inspection |
| --- | --- | --- |
| Weekday opening and closing | 9 AM and 6 PM, citation `[1]` | Both facts occur in source 1, original lines 3–5. |
| Follow-up about weekends | Reservation required; exact weekend hours unspecified, citation `[1]` | Source 1 states the reservation rule and does not state weekend hours. No unsupported hours were invented. |

Both responses address the questions and their factual claims are supported by
the supplied excerpt. Citation 1 is attached to the answer's factual paragraph in
each case. This inspection does not substitute for the frozen v11 judge in the
separate paired experiment.

## Measurement and provenance

[run.json](run.json) retains the complete metric inventory, settings, code hashes,
command, timestamps, duration and pass/fail counts. [browser.log](browser.log)
retains the output. Runtime code was unchanged from `47042b4`; the acceptance test
was committed in `264c1e5`. GPT-4.1, text-embedding-3-small and local BGE reranking
were enabled. Concurrency was one browser worker and two sequential questions;
there were no test or SDK retries.

Observed submit-to-visible-completion times were 1.820 and 2.321 seconds. These
include browser polling and are **not** first-answer-delta or precise HTTP
completion measurements. Request-stage timings and formatted evidence tokens
are retained in the history responses. Provider usage, billed cost, independent
search/fusion duration and index bytes before deletion are unavailable. The
separate paired RAG experiment measures the service's first-delta and complete
response timings and records provider usage.

The browser ran while the paired experiment's judge was active. Provider and host
load were uncontrolled; these two timings are functional diagnostics, not a
performance comparison. Logs retain non-failing Hugging Face authentication and
terminal-color warnings. No application stream cleanup warning appeared here.

Reproduce with a new run ID after building the frontend:

```bash
PYTHONPATH=. uv run --locked python evals/library-runs/20260925T002400Z-semantic-acceptance/run_browser.py NEW-RUN-ID
```

The user's existing library and `.env` were not changed. Feature acceptance and
merge approval remain the user's decision.
