# Final correction-session audit

`preflight-1`: 1 passed, 1 skipped. The high-effort comparison differs from low
only by the effort setting; cases, messages, roles, sources and annotations are
unchanged. Post-run test skips before outputs exist.

[Full backend checks](../20260925-grounding-reasoning/README.md): 561 passed,
1 intentionally skipped live-provider test. All earlier check/collection failures
are retained. No frontend change; earlier browser/build results are reused.

The final artifact audit covers all five attempts, every preserved provider delta,
original user messages and source bytes, requested model/effort, frozen hashes,
claim/source quote offsets, per-case decisions, complete metric inventory and
current documentation links. Passing this audit does not change the failed live
semantic verdict. Documentation uses English; unedited raw generated answers in
review artifacts retain the observed non-English token as failure evidence.

`final-audit-1`: **8 passed**. All five attempts and documentation checks above
pass integrity verification. This is not semantic acceptance: final candidate
remains 4/5 under frozen factual gates, with a separately recorded language defect.
Final content review confirms that readiness documents distinguish the current
GPT-4.1 default from candidate models and preserve the user's merge authority.
