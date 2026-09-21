# Local MVP release and evaluation report

Date: 2026-09-21 UTC (2026-09-20 America/New_York). Evaluated implementation: `689d49c8b8bc6100451d85d6a55e82749b094726`.

## Decision

The local, single-user TXT MVP is functional and ready for exploratory personal use with source inspection. It is **not validated as a reliable autonomous policy adviser**. The final real-provider browser workflow passed; the 25-question development evaluation completed, but Codex inspection identified answer-quality issues in six cases. Functional success, retrieval coverage, and semantic correctness are different results.

## Delivered behavior

- Upload UTF-8 TXT, index it, show processing/ready/failed states, and retrieve ready files only.
- Ask questions with streaming answers, inspect numbered original excerpts, continue a conversation, and restore completed exchanges after refresh.
- Stop generation without saving a partial answer; delete indexed files while retaining historical evidence snapshots.
- Recover abandoned uploads on startup. A process lock prevents recovery from treating another live process's upload as a crash.
- Preserve the original question during generation; a rewritten question is only a retrieval/reference-resolution hint.
- Run the built UI and API together with `make app`; stop project listeners with `make stop`.
- Default: `gpt-4.1` for generation and follow-up resolution, `text-embedding-3-small`, 2048-character chunks, 256-character overlap, cosine similarity, top-k 5. `ANSWER_MODEL` is configurable in `.env`.

The existing local library was verified against the frozen corpus hashes before reindexing. All 16 documents are ready, with 70 chunks. One saved conversation and ten messages were preserved. The previous database and vector index are backed up in ignored local directory `data/backups/pre-mvp-20260921T004213Z/`; its `reindex.json` maps old to new file IDs. Historical excerpts remain readable and are marked as originating from the replaced files. No credentials or local database backups are committed.

## Engineering verification

| Check | Observed result |
| --- | --- |
| Backend tests on final implementation | 253 passed, 1 skipped |
| Frontend unit tests | 29 passed |
| TypeScript and production build | Passed |
| Offline browser tests | 8 passed, including desktop/tablet/mobile |
| Port-stop regression | 1 passed |
| Final real-provider browser workflow | 1 passed; 8 completed answers, 1 cancelled turn |
| Actual local application after restart | `/` returned HTML 200; `/api/files` returned 16 ready files |
| Data preservation | Conversation/message counts match the pre-reindex backup |

The skipped backend test is the opt-in provider smoke test; separate paid browser and evaluation runs exercised the real providers. The backend suite reports one upstream AnyIO/Starlette deprecation warning. Frontend unit tests ran before the final backend-only default/prompt changes; the final production build and browser tests ran afterward.

The [final browser record](../browser-runs/20260921T004020061Z-030b4c7a/README.md) includes raw responses and screenshots. It checks upload, citations, weekday/weekend follow-up, refresh, cancellation, deletion, a study concept, year-specific printer instructions and price follow-up, conflicting notices, and missing personal account information. Explicit fixture assertions passed; Codex also inspected the eight actual answers and screenshot. This is one synthetic scenario, not eight independent benchmark samples or a reliability estimate.

A [pre-release browser run](../browser-runs/20260921T003005804Z-2722eff5/README.md) passed UI assertions but failed semantic inspection. Its raw artifacts remain unchanged. It exposed answer-like rewrites replacing the original question and a lost year in a follow-up. Those observations motivated the question-preservation fix and stronger acceptance assertions. No failed attempt was overwritten or relabeled as successful.

## Evaluation design

The final run used 16 frozen English NYU TXT documents and 25 revision-2 questions: 20 answerable and 5 unanswerable. Each question ran independently through the production `answer_question` service against a new isolated index. Gold references and expected points never entered the generation prompt. Original outputs, retrieval offsets, configuration, code hashes, and corpus/dataset hashes are retained.

- [Final run metadata](../runs/20260921T004017Z-5e4ee17d/run.json)
- [All answers, references, and retrieved excerpts](../runs/20260921T004017Z-5e4ee17d/reports/20260921T004111Z-b87c3edf.md)
- [Machine-readable diagnostics](../runs/20260921T004017Z-5e4ee17d/reports/20260921T004111Z-b87c3edf.json)
- [Codex qualitative audit](2026-09-21-mvp-answer-audit.json)

Revision 2 aligns questions with their requested answer points, including waiver materials and the course-plan caveat. It also asks about CPT source context without supplying the expected answer in the question. Previous dataset versions are retained in their run directories and are not directly comparable to revision 2.

## Final observed results

| Metric | Result | Interpretation |
| --- | --- | --- |
| Successful generation | 25/25 | Requests completed, not correctness |
| Generation errors | 0/25 | This one run only |
| Mean annotated-character recall | 85.83% | Mean covered reference characters, averaged within and then across answerable cases |
| Mean fully covered reference-span fraction | 85.83% | Reference-span coverage, not the percentage of fully answered questions |
| Invalid citation IDs | 0/25 answers | IDs exist; this does not establish supporting evidence |
| Answers without numbered citations | 1/25 | The personal-schedule refusal also added uncited factual background |
| Per-question latency p50 / p95 | 1.73 s / 3.64 s | Query embedding, retrieval and generation; excludes indexing and follow-up resolution |
| Core missing-information behavior | 5/5 unanswerable cases acknowledged missing specifics | Codex inspection; some still added problematic extra claims |
| Codex inspection findings | 6 cases need revision; 19 had no issue identified in this inspection | Developer-model review, not calibrated accuracy or independent human approval |
| Independent semantic pass rate | Not established | No fabricated human grades or reused invalid judge scores |

Latency was recorded while the browser acceptance ran concurrently. Provider/network variation and single samples prevent a latency-improvement claim. The corpus is a saved September 7 snapshot, not a current NYU information service. The development set was used to inspect and choose configurations; it is not a held-out test set.

## All-case qualitative audit

Reviewer: Codex, the same coding assistant that implemented the changes. Each answer was compared with expected points and relevant retrieved excerpts. “No issue identified” is a limited inspection result, not a guarantee of full semantic correctness. The JSON audit binds these notes to the exact saved answers with SHA-256 hashes. These observations are intentionally separate from the evaluator's human/LLM-judge score tables.

| Case | Finding | Evidence or remaining issue |
| --- | --- | --- |
| policy-scope | Needs revision | Sources [1][2] describe enforcement-procedure exceptions; the answer broadens them into exceptions to policy coverage, despite [3] covering all locations. |
| policy-fire | No issue identified | Immediate evacuation is explicitly supported by [2]. |
| policy-ai-impersonation | No issue identified | The consent restriction and AI impersonation prohibition match [1]. |
| policy-off-campus | No issue identified | Both substantial disruption and threats to health/safety/security appear in [1]. |
| msds-credits | No issue identified | [1] supports four times nine credits and the availability caveat; the answer labels the 36-credit inference from the sample plan. |
| msds-gpa | Needs revision | Misses 3.0 GPA and 66% completion. It fabricates a quotation about probation/dismissal and attributes it to [4], which is a list of links. |
| msds-independent-study | No issue identified | Six-credit limit and DS-GA 1010 match [2]. |
| msds-waiver | No issue identified | Only DS-GA 1002; transcripts, highlighted courses/grades, translated syllabi and optional website are present in [1]. |
| msds-industry | No issue identified | [1][2] support first-year practical training, mandatory internship, and two Big Data/NLP electives worth six credits. |
| msds-research | No issue identified | [1] explicitly excludes external participants. |
| msds-online | Needs revision | Refuses because the relevant FAQ passage was not retrieved; the frozen corpus does contain “No, we do not have an online program.” |
| missing-personal-schedule | Needs revision | Correctly refuses the personal timetable, but adds first-semester/course-search background without numbered citations. |
| msds-admissions-prerequisites | No issue identified | [1] supports mathematics, CS-101, the additional course choice, and Python/R experience without a fixed language requirement. |
| msds-gre-submission | No issue identified | [1][4][5] support optional GRE, unofficial PDF destination and separate official score submission. |
| msds-tracks-change | No issue identified | [2] names both tracks and the second-semester deadline. |
| msds-working-enrollment | No issue identified | Retrieved FAQ excerpts support six or fewer credits for full-time workers, no evening guarantee and the summer exception. |
| msds-pathbreaker-fall2027 | No issue identified | [1] states two awards, 36 points of tuition/fees and automatic consideration. |
| msds-capstone-fall2026-deadline | No issue identified | [2] includes August 16, 2026, closed submissions and the September 7 snapshot date. |
| policy-effective-date | No issue identified | [1][2] distinguish August 13, 2026 from the superseded August 15, 2025 policy. |
| msds-cpt-source-context | Needs revision | Retrieves first-year concentration details but misses the FAQ's after-first-year passage; incorrectly generalizes missing retrieval into “the admissions FAQ does not specify.” |
| msds-career-advising | No issue identified | [1][2] support the advising topics and Wasserman collaboration. |
| missing-fall2027-application-deadline | No issue identified | Refuses exact date/time/time zone; [2] says application details are coming soon. |
| missing-personal-scholarship-award | No issue identified | Separates limited/general scholarships from the user's unknown award status and amount. |
| missing-personal-capstone-team | Needs revision | Correctly refuses personal assignment but describes past project material as upcoming/future Fall 2026 themes without that support in cited [1]. |
| missing-exact-tuition-bill | No issue identified | Refuses a dollar total; keeps scholarship coverage separate from a universal tuition entitlement. |

The most consequential remaining failures are unsupported policy interpretation and a fabricated quotation in the GPA answer. Prompt instructions reduced neither to zero; the report does not claim otherwise. Missing sources must not be treated as proof that a whole document lacks information.

## Configuration evidence and limits

| Run | Model | Chunk / overlap (characters) | Annotated-character recall |
| --- | --- | --- | --- |
| [256 baseline](../runs/20260921T003629Z-ff051da4/run.json) | gpt-4.1-mini | 256 / 64 | 54.47% |
| [1024 candidate](../runs/20260921T003629Z-095dfa2a/run.json) | gpt-4.1-mini | 1024 / 128 | 74.33% |
| [2048 candidate](../runs/20260921T003755Z-005eed46/run.json) | gpt-4.1 | 2048 / 256 | 85.83% |
| [Final release](../runs/20260921T004017Z-5e4ee17d/run.json) | gpt-4.1 | 2048 / 256 | 85.83% |

Top-k remained 5; embeddings and revision-2 dataset were held constant. Chunk size and overlap changed together, and the final candidate also changed model. This supports selecting a more complete evidence window on this development set, not a causal answer-quality gain attributable to one factor. More text and a larger model increase token usage; this task did not measure token costs. Larger windows still missed GPA, online-program and part of the CPT evidence. They also introduced or retained opportunities for unrelated elaboration.

The older automated judge produced evidence-validation failures and semantic scoring errors; see the [judge calibration audit](2026-09-21-judge-calibration.md). We did not turn those scores into release accuracy. The generated final report therefore correctly leaves formal rubric scores pending, while this report provides a complete qualitative inspection of all 25 responses.

## Reproduce and use

Follow the [root quickstart](../../README.md), then open <http://127.0.0.1:8000>.

```bash
make test
make test-frontend
make test-browser
make test-stop
# The next two commands use paid real provider calls.
make test-browser-live
uv run --locked python -m evals.evaluate run --label "Reproduce local MVP release"
```

Use a new conversation for independent questions. Ask precise document-specific questions and inspect the displayed excerpts. Existing uploads elsewhere retain their old chunks unless re-uploaded. Do not run two API/CLI processes against one data directory. `make stop` stops listeners on configured development/test ports and leaves saved data intact.

Next quality work should target the observed retrieval misses and unsupported expansions, then evaluate on a new held-out set with independent human review. Multi-user hosting, authentication, PDF ingestion, hybrid retrieval and reranking remain outside this TXT/basic-RAG MVP.
