# Retrieval Failure Diagnosis

Two previously observed semantic misses were inspected with local BGE inference,
without API calls. Widening the BM25 window and fused scoring pool to 40 while
reusing the original vector top-20 still missed the CPT sentence. This is not a
complete wider-vector experiment; it only rules out that specific lexical change.

Scoring whole unique parents from the original route union ranked the relevant
admissions/general FAQ parents first and second for working/enrollment, and the
industry/admissions parents first and fourth for CPT. The latter still competes
for the packing budget: its first four regions total 4502 raw text tokens, before
metadata. This motivated a separate evidence-budget ablation instead of claiming
that parent ranking alone fixes the omission.

`results.json` and `parent-results.json` retain all scored text and ranks. Use
`qualified-metrics.json`, which corrects the inappropriate generic offline-test
inventory initially copied into the exploratory run. Model loading is separate
in the run files. The initial parent loader failed on a JSON-string heading field;
its failure is recorded separately. The corrected command/output is in
`../../check-runs/20260925-retrieval-coverage/parent-diagnostic-2.*`.

No answer quality, production latency, provider cost or general retrieval
improvement is claimed from these two exploratory cases. The completed feature
has its own frozen comparison under `../20260925-parent-reranking/`.
