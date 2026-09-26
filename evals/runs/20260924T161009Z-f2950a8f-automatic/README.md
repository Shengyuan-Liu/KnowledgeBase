# Automated RAG evaluation

Run: `20260924T161009Z-f2950a8f-automatic`

RAG observation origin: /Users/lucas/Documents/Projects/KnowledgeBase/evals/runs/20260924T154305Z-4ef1ccf3-automatic

Development/regression set; not held-out accuracy.
LLM judgments are assessments, not human ground truth; inventory misclassification and semantic errors remain possible.
In-process production streaming service, excluding app HTTP transport; no warmup, caches and host/provider load uncontrolled.

Metric | Value | N / status
--- | --- | ---
recall_at_k | 0.7795 | 16
precision_at_k | 0.3500 | 16
hit_rate_at_k | 0.9375 | 16
mrr_at_k | 0.9375 | 16
ndcg_at_k | 0.8336 | 16
annotated_char_recall | 0.9996 | 16
full_evidence_recall | 0.6875 | 16
answer_correctness | 1.0000 | 15
answer_completeness | 1 | 15
fully_correct_points | 1 | 15
faithfulness | 0.9778 | 15
answer_relevance | 1.0000 | 15
citation_support | 0.9917 | 15
citation_coverage | 0.6456 | 15
appropriate_abstention | 1 | 1
incorrect_abstention | 0 | 14
answerable_refusal | 0 | 14
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 1 | 15
unsupported_claims | 3 | 15
claim_count | 165 | 15
first_delta_seconds | mean=4.063s, p50=4.042s, p95=5.499s | 18
total_seconds | mean=5.347s, p50=5.272s, p95=7.974s | 18
generation_seconds | mean=2.159s, p50=1.841s, p95=4.809s | 18
generation_first_delta_seconds | mean=0.882s, p50=0.707s, p95=2.340s | 18
retrieval_seconds | mean=3.182s, p50=3.159s, p95=3.720s | 18
embedding_seconds | mean=0.332s, p50=0.302s, p95=0.680s | 18
rerank_seconds | mean=2.826s, p50=2.862s, p95=3.432s | 18
packing_seconds | mean=0.003s, p50=0.002s, p95=0.006s | 18
search_fusion_seconds | unavailable | Production service exposes total retrieval, embedding, rerank and packing; search/fusion not independently timed.
reliability | {"attempted": 18, "planned": 18, "success": 18, "errors": 0, "not_attempted": 0, "success_rate": 1.0, "timeouts": 0, "retries": 0} | 18
judge_reliability | {"reviewed": 18, "valid": 15, "invalid_or_error": 3, "pending": 3} | 18
judge_seconds | mean=32.585s, p50=25.934s, p95=92.252s | 18
token_usage.ingestion | {"total_tokens": 26199, "prompt_tokens": 26199} | 17
token_usage.query_embedding | {"total_tokens": 429, "prompt_tokens": 429} | 18
token_usage.generation | {"input_tokens": 61600, "output_tokens": 2992, "total_tokens": 64592} | 18
token_usage.judge | {"input_tokens": 221818, "output_tokens": 106163, "total_tokens": 327981} | 36
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [3098, 3098, 3271, 3655, 3703, 4009, 3800, 3405, 3871, 3778, 3594, 3569, 249, 951, 3176, 1113, 1923, 1518] | 18
concurrency_throughput | unavailable | No comparable RAG batch wall interval recorded.
ingestion | {"seconds": 7.463589709019288, "files": [{"file_name": "anthropic_api.md", "seconds": 0.9733090410009027, "bytes": 5643}, {"file_name": "university-student-conduct-policy.txt", "seconds": 1.1409382920246571, "bytes": 21406}, {"file_name": "student-resources-overview.txt", "seconds": 0.4701649999478832, "bytes": 2275}, {"file_name": "student-career-development-professional-development-overview.txt", "seconds": 0.22576125001069158, "bytes": 2860}, {"file_name": "student-career-development-professional-career-information.txt", "seconds": 0.2248847089940682, "bytes": 873}, {"file_name": "masters-in-data-science-tracks.txt", "seconds": 0.32023266702890396, "bytes": 4055}, {"file_name": "masters-in-data-science-summer-research-initiative.txt", "seconds": 0.27138766599819064, "bytes": 1752}, {"file_name": "masters-in-data-science-overview.txt", "seconds": 0.24094695888925344, "bytes": 2728}, {"file_name": "masters-in-data-science-industry-concentration.txt", "seconds": 0.5179713749093935, "bytes": 3292}, {"file_name": "masters-in-data-science-financial-aid-fellowships.txt", "seconds": 0.32595879200380296, "bytes": 4136}, {"file_name": "masters-in-data-science-faq.txt", "seconds": 0.40631724998820573, "bytes": 15140}, {"file_name": "masters-in-data-science-faq-general.txt", "seconds": 0.34853125002700835, "bytes": 9840}, {"file_name": "masters-in-data-science-capstone.txt", "seconds": 0.4180574589408934, "bytes": 9715}, {"file_name": "masters-in-data-science-admissions-ambassadors.txt", "seconds": 0.27229637501295656, "bytes": 5917}, {"file_name": "data-science-ms-bulletin.txt", "seconds": 0.4132163330214098, "bytes": 11433}, {"file_name": "curriculum.txt", "seconds": 0.3908102500718087, "bytes": 9132}, {"file_name": "admissions-requirements.txt", "seconds": 0.5019137909403071, "bytes": 8202}], "index_bytes": 2402468, "indexed_chunks": 92} | 17
update_delete | not_applicable | Evaluation creates a fresh isolated corpus; update/delete lifecycle is not exercised.
model_loading | 4.2172 | 1

## Previous evaluation

Previous: `evals/library-runs/20260924T150609Z-source-metadata-v2`

## Pending judge reviews

Case | Reason
--- | ---
msds-waiver | Judge reported inventory issues; review is incomplete.
missing-personal-schedule | Judge reported inventory issues; review is incomplete.
api-setup | Judge reported inventory issues; review is incomplete.

Metric | Previous | Current | Delta
--- | --- | --- | ---
recall_at_k | 0.7795138888888888 | 0.7795138888888888 | 0.0
precision_at_k | 0.35000000000000003 | 0.35000000000000003 | 0.0
hit_rate_at_k | 0.9375 | 0.9375 | 0.0
mrr_at_k | 0.9375 | 0.9375 | 0.0
ndcg_at_k | 0.833565316812447 | 0.833565316812447 | 0.0
annotated_char_recall | 0.9995716773984152 | 0.9995716773984152 | 0.0
full_evidence_recall | 0.6875 | 0.6875 | 0.0
generation_seconds | {'mean': 2.4964175393365116, 'p50': 2.220790520950686, 'p95': 5.130264999927022} | {'mean': 2.159451382014797, 'p50': 1.8406282705254853, 'p95': 4.808744209003635} | {'mean': -0.33696615732171464, 'p50': -0.3801622504252009, 'p95': -0.3215207909233868}
generation_first_delta_seconds | {'mean': 0.8760669260130575, 'p50': 0.7420645000529476, 'p95': 3.643484584055841} | {'mean': 0.8815688171760283, 'p50': 0.7067252499982715, 'p95': 2.340421500033699} | {'mean': 0.00550189116297084, 'p50': -0.035339250054676086, 'p95': -1.303063084022142}
packing_seconds | {'mean': 0.005511416626783709, 'p50': 0.005242646031547338, 'p95': 0.01130729098804295} | {'mean': 0.0026652686841165027, 'p50': 0.0021984585328027606, 'p95': 0.005625209072604775} | {'mean': -0.0028461479426672063, 'p50': -0.003044187498744577, 'p95': -0.005682081915438175}
judge_seconds | {'mean': 32.35662671989606, 'p50': 29.738538041478023, 'p95': 75.30819995806087} | {'mean': 32.584688196605484, 'p50': 25.93406345800031, 'p95': 92.25240229105111} | {'mean': 0.22806147670942067, 'p50': -3.804474583477713, 'p95': 16.944202332990244}

### Paired valid-review subset

Only identical case IDs with valid applicable reviews on BOTH sides under the same judge protocol; failures excluded, selection bias possible. Not a full-set comparison.

Metric | Previous | Current | Delta | Pairs
--- | --- | --- | --- | ---
answer_correctness | 1.0000 | 1.0000 | +0.0000 | 15
answer_completeness | 1.0000 | 1.0000 | +0.0000 | 15
fully_correct_points | 1.0000 | 1.0000 | +0.0000 | 15
faithfulness | 0.9809 | 0.9778 | -0.0031 | 15
answer_relevance | 1.0000 | 1.0000 | +0.0000 | 15
citation_support | 0.9811 | 0.9917 | +0.0106 | 15
citation_coverage | 0.6623 | 0.6456 | -0.0168 | 15
appropriate_abstention | 1.0000 | 1.0000 | +0.0000 | 1
incorrect_abstention | 0.0000 | 0.0000 | +0.0000 | 14
answerable_refusal | 0.0000 | 0.0000 | +0.0000 | 14

Positive timing deltas mean slower. Fractions are not percent points. Single-pass uncontrolled comparisons are descriptive, not causal.
Quality comparable: False; full-pipeline timing comparable: False.

### Per-question quality

Case | Previous correctness | Current correctness | Previous faithfulness | Current faithfulness
--- | --- | --- | --- | ---
policy-ai-impersonation | 1.0000 | 1.0000 | 1.0000 | 1.0000
policy-off-campus | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-credits | 1.0000 | 1.0000 | 0.9474 | 1.0000
msds-gpa | 1.0000 | 1.0000 | 1.0000 | 0.8333
msds-waiver | 1.0000 | unavailable | 1.0000 | unavailable
msds-industry | 1.0000 | 1.0000 | 1.0000 | 1.0000
missing-personal-schedule | 1.0000 | unavailable | 0.6667 | unavailable
msds-admissions-prerequisites | 1.0000 | 1.0000 | 1.0000 | 0.9333
msds-working-enrollment | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-pathbreaker-fall2027 | 1.0000 | 1.0000 | 0.9091 | 0.9000
msds-cpt-source-context | 1.0000 | 1.0000 | 1.0000 | 1.0000
missing-exact-tuition-bill | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-setup | unavailable | unavailable | unavailable | unavailable
api-model-mapping | 1.0000 | 1.0000 | 0.8571 | 1.0000
api-top-p | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-thinking | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-images | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-tools | 1.0000 | 1.0000 | 1.0000 | 1.0000

Definitions: [metrics guide](../../metrics.md).
