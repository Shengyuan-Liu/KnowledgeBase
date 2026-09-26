# Evidence Packing Comparison

Status: implemented and measured on `v1`; user acceptance and merge approval are pending.
The directory name records the initial child-first experiment. The shipped policy
is **`parent_then_child`**, not either strict child-first prototype.

## Change and decision

The previous BGE run retrieved the CPT FAQ child, but its full parent did not fit
the 4,096-token context budget. The old packer discarded that child along with its
parent. The new packer keeps every parent admitted by the original algorithm,
then uses remaining budget for complete selected children of omitted parents.
It retains retrieval order, exact source slices and provenance, without additional
retrieval, truncation, or duplicate parent/child text. `parent_first` remains an
explicit control. The default is shared by the API, CLI and evaluation runner.

The initial strict child-first reservation prototype recovered CPT coverage from
50% to 100%, but reduced GPA coverage from 100% to 0%. Expanding cheaper parents
first did not resolve that regression. The needed GPA fact was in an unselected
sibling and depended on parent expansion. Both rejected algorithms and all 54
replay records are preserved in `rank_order_packing.py`, `cost_order_packing.py`
and `packing-replay.jsonl`. The final algorithm's 18 fixed-candidate replays are
in `parent-then-child-replay.jsonl`. There are no question-specific rules.

## Controlled workload

- The same 18 frozen questions and annotations as the
  [preceding BGE comparison](../20260924T002009Z-bge-serialized/README.md):
  16 annotated answerable questions and two unanswerable questions.
- The same 17 Ready files, 38 parents and 92 children, copied into a temporary
  isolated library while the source API was stopped. No files were reuploaded,
  deleted, re-embedded or rechunked. `cases.json` and `chunks.json` preserve inputs.
- Hybrid BM25/vector retrieval, RRF, top-k 5, candidate window 20, exact numbered
  evidence budget 4,096 `cl100k_base` tokens, GPT-4.1 answer generation and
  `text-embedding-3-small` embeddings were unchanged.
- Local `BAAI/bge-reranker-v2-m3`, revision
  `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, Apple MPS, float32,
  batch size 4, maximum pair length 1,024; aggregate pair-text budget 16,384.
- 36 real HTTP streaming requests, one per strategy/question, concurrency 1,
  alternating strategy order. No query warmup. Cached weights loaded before
  requests; server startup including model loading took 4.565 seconds and is
  excluded from per-query times. First-query cold kernel effects remain included.
  The reranker lock is uncontended at concurrency 1; stage timing includes its
  call, including lock acquisition. Network and host load are uncontrolled;
  some offline checks also ran during the comparison.
- `run.json` records settings, model revision, base commit and tracked diff hash.
  The implementation and harness are in the same Git commit as this report;
  the recorded diff hash alone does not cover then-untracked new files.
  `implementation-sha256.json` records the delivered backend and evidence-panel
  file hashes, including the new packing module.
- The evaluation-only routes call the production streaming conversation service.
  Every saved answer/source/diagnostic snapshot was checked against the complete
  event. No evaluation conversations were added to the daily library.

## Results

All 36 requests completed, with zero recorded request errors. `audit.json`
confirms identical selected child IDs and reranked ID order for every pair,
preservation of all previously admitted sources, exact stored text/metadata,
no parent/child duplication, and compliance with the numbered context budget.

| Metric | Parent-first control | Parent then child |
| --- | ---: | ---: |
| Annotated character recall, mean over 16 cases | 96.83% | 99.96% |
| Fully covered evidence-span recall, mean over 16 cases | 65.63% | 68.75% |
| CPT character / full-span recall | 50% / 50% | 100% / 100% |
| GPA character / full-span recall | 100% / 100% | 100% / 100% |
| Mean supplied evidence tokens | 2,749.22 | 2,918.22 |

CPT is the only coverage improvement; all other per-case values are unchanged.
The remaining character gaps are at annotated Markdown region boundaries; the
unchanged all-or-nothing span metric remains much lower. Neither metric measures
whether the answer actually used or correctly interpreted the evidence.

Times below are seconds, with 18 samples per strategy. Percentiles use nearest
rank, so P95 is the maximum of this small sample.

| Timing | Control mean / P50 / P95 | New mean / P50 / P95 |
| --- | ---: | ---: |
| First nonempty answer delta | 3.626 / 3.549 / 5.046 | 3.452 / 3.487 / 3.831 |
| Complete HTTP response | 5.165 / 4.881 / 8.137 | 4.814 / 4.842 / 6.337 |
| Local reranking stage | 2.629 / 2.671 / 2.906 | 2.621 / 2.678 / 2.904 |
| Evidence packing stage | 0.00165 / 0.00167 / 0.00334 | 0.00192 / 0.00162 / 0.00449 |

First-delta timing starts before POST and stops at the first nonempty
`answer_delta`, not the earlier `start` or `sources` event. Complete HTTP timing
stops after consuming the response; each row also stores the earlier complete
event timestamp. History validation is excluded. These are single-pass
observations, not evidence that the new algorithm speeds up generation. The
measured packing overhead is about 0.27 ms on average. Do not compare these
sequential timings directly to the preceding three-worker BGE experiment.

Local reranking has no paid rerank-provider call. Embedding and answer requests
use the existing configured provider. Provider token usage and billed cost were
not captured and are unavailable; evidence tokens are not billed input tokens.

## Answer review and unresolved issues

`reviews.jsonl` contains focused Codex development reviews against exact supplied
sources and expected points, with both strategy outputs for CPT, GPA, API setup,
off-campus policy and the two unanswerable cases. This is not independent human
grading and does not establish an aggregate answer-accuracy score. The cases
were used to develop the policy; they are not held-out validation.

- **CPT is still an answer failure in the paired run.** Both pages are now
  supplied, but GPT-4.1 ignores the retained FAQ child and incorrectly says the
  FAQ has no timing statement. The new packer repairs evidence availability,
  not this generation failure. Coverage is 100% while this answer still fails.
- GPA retains the correct 3.0 GPA and 66% credit-completion requirements. The
  strict prototypes' regression is avoided.
- API setup answers supply the requested SDK, environment variables and call
  method, but still omit `anthropic.Anthropic()` from the broader expected-point
  rubric. That rubric asks for more than the question explicitly requests;
  neither the question nor annotation was changed for this comparison.
- Both unanswerable cases acknowledge missing personal schedule or exact tuition
  data. Citation syntax alone was not used as a quality judgment.

After rebuilding the frontend, the daily API was restored on port 8000. One
additional CPT streaming smoke request checked the real route, retained child,
saved history and frontend. It took 4.445 seconds to first delta and 6.969 seconds
to finish; it is not included in the 36-request comparison. All seven existing
conversations remained readable, and all 17 files were unchanged. That sample
did quote both timing statements, but inferred a general-versus-concentration
eligibility distinction beyond the wording of the sources. This variability is
further reason to leave CPT answer quality unresolved. One smoke conversation
was added to the daily history; `app-smoke.json` preserves its exact output.

## Verification and artifacts

- Backend: 476 passed, 1 skipped (live-provider test is opt-in).
- Frontend: 34 passed; TypeScript check and production build passed.
- Browser: 9 passed at the existing desktop/mobile viewport cases.
- New regression coverage: exact boundary budgets, complete fenced code and
  CRLF/Unicode preservation, retained siblings, mixed flat/parent contexts,
  JSON/SSE provenance, and saved child evidence after restart and source deletion.
- `answers.jsonl`: all 36 event streams, first-delta/complete/total times,
  exact answers, selected candidates, BGE rankings, supplied sources,
  exclusions, unexpanded parents and per-case coverage.
- `summary.json`, `audit.json`, `reviews.jsonl`: aggregates, invariant checks,
  and focused answer judgments. `server.log` retains server execution output.
- `run_stream_comparison.py`, `stream_server.py`, replay scripts, `audit_run.py`,
  `run_smoke.py`: reproducible harnesses. Output writers refuse overwrites;
  use a new run directory for another measurement. Stop the source API before
  the harness copies its library. Run repository-importing scripts with the
  repository root in `PYTHONPATH`.

Next acceptance work should address multi-source answer completeness and source
attribution, then repeat a controlled comparison. Passing tests and restoring
coverage do not authorize a merge.
