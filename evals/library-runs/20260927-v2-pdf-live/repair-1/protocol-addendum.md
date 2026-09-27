# Repair comparison, frozen before replay

Replay all 16 cases in both arms using the same existing five-PDF index and
`../effective-cases.json`. Preserve the initial pass unchanged. No parser,
embedding, reranking, context-format, packing or budget changes. The product
changes are query-local representative selection, explicit assessor quote and
filename instructions (prompt v2), and recognition of the observed leading
"Using only" source clause. The latter also affects single mode.

This is a development repair pass, not an independent held-out evaluation.
Live plans and completions remain stochastic. Compare frozen point-level
annotations; retain failures and quality losses. Do not claim causal attribution
for every changed answer. The known dense-table extraction and parent-priority
packing limitations remain in the workload. Do not raise budgets or remove cases
to make the provisional acceptance gates pass.

The original `record_check.py` wrapper was intended for offline tests. Its generic
not-applicable inventory on the live ingestion/answer commands is erroneous;
`../measurement.json` is the authoritative append-only supplement for live
measurements. Raw command records and outputs are preserved unchanged.
