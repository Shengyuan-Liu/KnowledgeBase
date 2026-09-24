# Important Notes

- Use English for all project documentation and text content, including UI text, prompts, comments, examples, and commit messages. Do not add Chinese text to the project.
- After completing each change, create a corresponding Git commit so that the change can be tracked and rolled back later.
- For code changes, write or update the relevant tests and ensure that all applicable tests and verification checks pass before delivery. For documentation-only changes, review the content and check links and formatting; automated tests are not required.
- Use `.env` for local environment configuration and credentials, and keep it out of Git. Use `.env.example` for placeholders. Introduce a `Settings` class only when current configuration needs justify it.

# v1 Branch and Merge Workflow

- Perform all v1 development on the `v1` branch and commit changes there.
- The user decides when each v1 feature is complete. Passing tests or finishing implementation does not authorize a merge.
- Merge each feature into `main` only after the user explicitly authorizes that feature's merge. Approval for one feature does not authorize later merges.
- After an authorized merge, continue subsequent v1 work on the `v1` branch.

# Test and Experiment Measurement

- For every future test or experiment, retain a run record following the [measurement policy](evals/measurement-policy.md), not only when replacing a component. Include the complete metric inventory with measured values or explicit `not_applicable` / `unavailable` status and a reason; never silently omit a metric or replace missing data with zero.
- Measure retrieval Recall@K, Precision@K, Hit Rate@K, MRR, NDCG@K, and final supplied-evidence coverage when applicable. State K, relevance labels, evaluation unit, stage and aggregation. Use stable source spans or facts when comparing different chunk boundaries; distinguish candidate retrieval, reranking and evidence packing.
- Measure answer correctness, faithfulness, completeness, relevance, citation support, citation coverage and abstention behavior when applicable. Record both appropriate abstention on unanswerable cases and incorrect abstention on answerable cases. Fix the rubric/reviewer protocol, preserve claim-level or expected-point evidence, and manually inspect representative failures. LLM judgments are assessments, not ground truth.
- Measure first-answer-delta and complete-response latency, stage timings, token usage and cost, success/error/timeout/retry rates, concurrency/throughput, and ingestion time/index size/update/delete behavior when applicable. Report quality and performance separately.
- Offline unit/integration tests must record scope, command, code version, duration, pass/fail/skip counts and failures. Mark live quality, provider cost and production performance metrics as not applicable to mocked tests; do not run paid benchmarks merely to fill those fields. Documentation-only changes require a recorded content/link/format review, not automated tests.

- When replacing or materially changing a RAG component, record a before/after comparison using the same frozen questions, corpus, and annotations. Keep other settings fixed where possible and disclose differences that limit comparison.
- Record complete-answer latency, time to first answer delta for streaming, and affected-stage latency separately. Include sample counts, mean and percentile timings, concurrency, device, and whether model loading or queue waiting is included. Mark unmeasured metrics as unavailable; never substitute total duration for time to first answer delta.
- Record evidence coverage separately from answer quality. Inspect actual answers and supplied evidence, preserve per-question improvements and regressions, and identify the reviewer and review method. Valid citation IDs alone do not establish support.
- Save resolved models and revisions, component settings, code version, exact retrieved and supplied evidence, rankings, budget exclusions, errors, and available token usage or cost information. Distinguish local compute from paid provider calls; do not invent billing figures.
- Keep evaluation artifacts append-only in a new run directory, including failed attempts. Link a concise comparison report from the relevant documentation. Missing measurements and known failures must remain visible in the delivery summary.
- Passing checks or improving an aggregate metric does not authorize a merge; the user decides acceptance and approves each feature's merge.

# Learning and Code Ownership

- The user intends to write most of the project's Python backend and MLE / AI Engineer code by hand. By default, Codex should explain each proposed code file's purpose, the responsibilities of its functions, and the underlying concepts, reasoning, and implementation guidance so the user can write the code.
- Only write or modify Python implementation code when the user explicitly asks Codex to do so. A request for an explanation, design, or guidance does not authorize implementation. Keep any authorized implementation within the requested scope.
- Exceptions: Codex may directly implement Python code explicitly marked with `# TODO` or `#TODO`, and may directly write or modify code in any language other than Python as needed for the user's task. A TODO marker authorizes only the associated unfinished code, not unrelated Python changes.

# Implementation Simplicity

- Keep code simple and focused on current requirements. Do not anticipate hypothetical failures or add defensive code before a concrete problem has been observed.
- Avoid speculative validation, fallback paths, response repair, and redundant checks of behavior already handled by a dependency. Add such handling only for an observed problem or an explicit requirement, and keep it limited to that need.
- Test required behavior and regressions from real problems. Do not invent hypothetical failure scenarios solely to justify defensive implementation.
