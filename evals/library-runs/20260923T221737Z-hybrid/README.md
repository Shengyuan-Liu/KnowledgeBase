# Live Hybrid Retrieval Comparison

On 2026-09-23, the same 18 frozen questions were run against both vector-only and
hybrid retrieval using the existing library: 17 Ready files, 38 parents, and 92
children. All 36 provider requests completed. No files were re-uploaded, and the
paired service evaluation did not write conversation history.

Both modes use `gpt-4.1`, `text-embedding-3-small`, five selected children, and a
4096-token evidence budget. Hybrid takes up to 20 hits per route, with BM25
`k1=1.2`, `b=0.75`, and RRF `k=60`. Vector takes five vector hits directly.
Three independent questions run concurrently. Models are stochastic; this is a
development comparison, not a held-out benchmark or a calibrated quality claim.

## Recorded results

| Metric | Vector | Hybrid |
| --- | ---: | ---: |
| Completed answers | 18/18 | 18/18 |
| Mean annotated character coverage | 90.58% | 93.71% |
| Mean fully covered gold-span fraction | 59.38% | 62.50% |
| Mean evidence tokens, including labels | 2586.83 | 2646.89 |
| Mean observed service duration | 2.59 s | 2.74 s |

Coverage averages over the 16 answerable questions, excluding two unanswerable
cases. It measures supplied source spans, not correctness. The full-span metric
is a mean of per-question span fractions, not a question pass rate. Near-100%
Markdown coverage can still miss annotated boundary whitespace. Latency includes
provider variability and concurrent requests; it is not a retrieval microbenchmark.

Every source matches its stored parent text and offsets, every numbered evidence
string fits the budget, and no answer contains an invalid citation ID. Citation
ID validity alone does not establish semantic support.

## Improvements and regression

| Question | Observed vector behavior | Observed hybrid behavior |
| --- | --- | --- |
| Academic progress / GPA | Correct general-FAQ parent is absent; answer abstains | Correct child reaches fused rank 4, parent fits, answer gives 3.0 GPA and 66% credit completion |
| CPT source comparison | Admissions FAQ child is fifth; its parent is excluded by the budget | Admissions FAQ child reaches fused rank 2; both pages fit and the answer distinguishes their timing and includes OGS advice |
| Markdown API setup | Complete setup parent is supplied | Same setup parent is supplied; no measured retrieval gain |
| Admissions prerequisites | Correct admissions parent is first; all prerequisite groups are answered | Correct child falls to fused rank 4; the parent is excluded, so the answer misses most prerequisite groups |

The prerequisite regression is a ranking-and-budget problem, not a failure to
find the correct child. Two preceding FAQ parents consume 3067 tokens; the
1312-token admissions parent cannot fit under 4096. It appears in `excluded`.
Simply increasing child top-k cannot restore it under the unchanged packing order.
This is a concrete case for evaluating the planned reranking stage before parent
expansion. No question-specific boost or silent budget increase was added.

Across all questions, character coverage changes only for GPA (+100 percentage
points), CPT (+50), and prerequisites (-100). The other 13 answerable questions
retain their coverage. The two unanswerable cases abstain from inventing personal
schedule details or dollar tuition totals in both modes.

[Targeted reviews](reviews.jsonl) cover the four rows above for both modes.
They are Codex reference-point inspections, not independent human ratings or a
calibrated LLM judge. No aggregate answer-accuracy claim is made. In the setup
case, the vector answer omits explicit client construction while the hybrid
answer includes it, even though both have the same evidence; that difference
must not be attributed to better retrieval.

## Artifacts and verification

- [run.json](run.json): resolved settings, start time, base revision, and worktree
  diff fingerprint. The implementation was uncommitted during the experiment;
  the commit containing this report also contains the tested implementation.
- [cases.json](cases.json): byte-identical copy of the earlier 18-case dataset,
  including reference points and source spans. Filenames are normalized to
  basenames only when comparing against uploaded-file names.
- [chunks.json](chunks.json): unchanged file IDs, child text, parents, and offsets.
- [answers.jsonl](answers.jsonl): each question, mode, duration, answer, full
  supplied sources, raw route hits, fused ranking, selected candidates, and exclusions.
- [summary.json](summary.json): automatic paired aggregates.
- [reviews.jsonl](reviews.jsonl): eight targeted reference-point reviews and issues.
- [verification.json](verification.json): byte-identical frozen cases, unchanged
  library snapshots, valid local documentation links, and five readable saved conversations.
- [app-smoke.json](app-smoke.json): real streamed GPA answer after restarting the
  application, plus a readback proving saved source/diagnostic equality. This one
  smoke exchange is saved in the active library and excluded from paired metrics.
- [run_evaluation.py](run_evaluation.py): one-run reproduction script. Run with
  `PYTHONPATH=.` from the repository root, after stopping the app that owns the
  data directory. Copy the runner and frozen cases into a new run directory
  first: existing artifacts are protected by exclusive-create writes.

Offline checks passed: 440 backend tests (one live-only test skipped), 32 frontend
tests, frontend build, and nine browser end-to-end tests. User feature acceptance
and merge authorization are still pending; this report does not authorize a merge.
