# Automated RAG evaluation

Run: `20260924T191633Z-0dae378e-automatic`

RAG observation origin: /Users/lucas/Documents/Projects/KnowledgeBase/evals/runs/20260924T161009Z-f2950a8f-automatic

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
answer_correctness | 0.9608 | 17
answer_completeness | 0.9706 | 17
fully_correct_points | 0.9510 | 17
faithfulness | 0.9882 | 17
answer_relevance | 1.0000 | 17
citation_support | 0.9739 | 17
citation_coverage | 0.6525 | 17
appropriate_abstention | 1 | 2
incorrect_abstention | 0 | 15
answerable_refusal | 0 | 15
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 0 | 17
unsupported_claims | 1 | 17
claim_count | 123 | 17
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
judge_reliability | {"reviewed": 18, "valid": 17, "invalid_or_error": 1, "pending": 1} | 18
judge_seconds | mean=33.312s, p50=25.459s, p95=88.718s | 18
token_usage.ingestion | {"total_tokens": 26199, "prompt_tokens": 26199} | 17
token_usage.query_embedding | {"total_tokens": 429, "prompt_tokens": 429} | 18
token_usage.generation | {"input_tokens": 61600, "output_tokens": 2992, "total_tokens": 64592} | 18
token_usage.judge | {"input_tokens": 201777, "output_tokens": 86278, "total_tokens": 288055} | 53
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [3098, 3098, 3271, 3655, 3703, 4009, 3800, 3405, 3871, 3778, 3594, 3569, 249, 951, 3176, 1113, 1923, 1518] | 18
concurrency_throughput | unavailable | No comparable RAG batch wall interval recorded.
ingestion | {"seconds": 7.463589709019288, "files": [{"file_name": "anthropic_api.md", "seconds": 0.9733090410009027, "bytes": 5643}, {"file_name": "university-student-conduct-policy.txt", "seconds": 1.1409382920246571, "bytes": 21406}, {"file_name": "student-resources-overview.txt", "seconds": 0.4701649999478832, "bytes": 2275}, {"file_name": "student-career-development-professional-development-overview.txt", "seconds": 0.22576125001069158, "bytes": 2860}, {"file_name": "student-career-development-professional-career-information.txt", "seconds": 0.2248847089940682, "bytes": 873}, {"file_name": "masters-in-data-science-tracks.txt", "seconds": 0.32023266702890396, "bytes": 4055}, {"file_name": "masters-in-data-science-summer-research-initiative.txt", "seconds": 0.27138766599819064, "bytes": 1752}, {"file_name": "masters-in-data-science-overview.txt", "seconds": 0.24094695888925344, "bytes": 2728}, {"file_name": "masters-in-data-science-industry-concentration.txt", "seconds": 0.5179713749093935, "bytes": 3292}, {"file_name": "masters-in-data-science-financial-aid-fellowships.txt", "seconds": 0.32595879200380296, "bytes": 4136}, {"file_name": "masters-in-data-science-faq.txt", "seconds": 0.40631724998820573, "bytes": 15140}, {"file_name": "masters-in-data-science-faq-general.txt", "seconds": 0.34853125002700835, "bytes": 9840}, {"file_name": "masters-in-data-science-capstone.txt", "seconds": 0.4180574589408934, "bytes": 9715}, {"file_name": "masters-in-data-science-admissions-ambassadors.txt", "seconds": 0.27229637501295656, "bytes": 5917}, {"file_name": "data-science-ms-bulletin.txt", "seconds": 0.4132163330214098, "bytes": 11433}, {"file_name": "curriculum.txt", "seconds": 0.3908102500718087, "bytes": 9132}, {"file_name": "admissions-requirements.txt", "seconds": 0.5019137909403071, "bytes": 8202}], "index_bytes": 2402468, "indexed_chunks": 92} | 17
update_delete | not_applicable | Evaluation creates a fresh isolated corpus; update/delete lifecycle is not exercised.
model_loading | 4.2172 | 1

## Previous evaluation

Previous: `evals/runs/20260924T161009Z-f2950a8f-automatic`

## Pending judge reviews

Case | Reason
--- | ---
policy-ai-impersonation | Judge reported inventory issues; review is incomplete.

Metric | Previous | Current | Delta
--- | --- | --- | ---
recall_at_k | 0.7795138888888888 | 0.7795138888888888 | 0.0
precision_at_k | 0.35000000000000003 | 0.35000000000000003 | 0.0
hit_rate_at_k | 0.9375 | 0.9375 | 0.0
mrr_at_k | 0.9375 | 0.9375 | 0.0
ndcg_at_k | 0.833565316812447 | 0.833565316812447 | 0.0
annotated_char_recall | 0.9995716773984152 | 0.9995716773984152 | 0.0
full_evidence_recall | 0.6875 | 0.6875 | 0.0
first_delta_seconds | {'mean': 4.063298046310795, 'p50': 4.04188516701106, 'p95': 5.499256415991113} | {'mean': 4.063298046310795, 'p50': 4.04188516701106, 'p95': 5.499256415991113} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
total_seconds | {'mean': 5.347337115614209, 'p50': 5.272389125020709, 'p95': 7.974267708021216} | {'mean': 5.347337115614209, 'p50': 5.272389125020709, 'p95': 7.974267708021216} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
generation_seconds | {'mean': 2.159451382014797, 'p50': 1.8406282705254853, 'p95': 4.808744209003635} | {'mean': 2.159451382014797, 'p50': 1.8406282705254853, 'p95': 4.808744209003635} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
generation_first_delta_seconds | {'mean': 0.8815688171760283, 'p50': 0.7067252499982715, 'p95': 2.340421500033699} | {'mean': 0.8815688171760283, 'p50': 0.7067252499982715, 'p95': 2.340421500033699} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
retrieval_seconds | {'mean': 3.181643377219896, 'p50': 3.1591814790153876, 'p95': 3.7204449999844655} | {'mean': 3.181643377219896, 'p50': 3.1591814790153876, 'p95': 3.7204449999844655} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
embedding_seconds | {'mean': 0.3316849490575906, 'p50': 0.30191489605931565, 'p95': 0.67991337494459} | {'mean': 0.3316849490575906, 'p50': 0.30191489605931565, 'p95': 0.67991337494459} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
rerank_seconds | {'mean': 2.826308094941649, 'p50': 2.8620931039913557, 'p95': 3.431701709050685} | {'mean': 2.826308094941649, 'p50': 2.8620931039913557, 'p95': 3.431701709050685} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
packing_seconds | {'mean': 0.0026652686841165027, 'p50': 0.0021984585328027606, 'p95': 0.005625209072604775} | {'mean': 0.0026652686841165027, 'p50': 0.0021984585328027606, 'p95': 0.005625209072604775} | {'mean': 0.0, 'p50': 0.0, 'p95': 0.0}
judge_seconds | {'mean': 41.09225105323518, 'p50': 34.72849574999418, 'p95': 87.85655700007919} | {'mean': 33.3124502176199, 'p50': 25.459434187505394, 'p95': 88.71750975004397} | {'mean': -7.7798008356152835, 'p50': -9.269061562488787, 'p95': 0.8609527499647811}
model_loading | 4.217207625042647 | 4.217207625042647 | 0.0

### Paired valid-review subset

Only identical case IDs with valid applicable reviews on BOTH sides under the same judge protocol; failures excluded, selection bias possible. Not a full-set comparison.

Metric | Previous | Current | Delta | Pairs
--- | --- | --- | --- | ---
answer_correctness | 0.9902 | 0.9608 | -0.0294 | 17
answer_completeness | 1.0000 | 0.9706 | -0.0294 | 17
fully_correct_points | 0.9804 | 0.9510 | -0.0294 | 17
faithfulness | 0.9840 | 0.9882 | +0.0042 | 17
answer_relevance | 1.0000 | 1.0000 | +0.0000 | 17
citation_support | 0.9774 | 0.9739 | -0.0036 | 17
citation_coverage | 0.6370 | 0.6525 | +0.0156 | 17
appropriate_abstention | 1.0000 | 1.0000 | +0.0000 | 2
incorrect_abstention | 0.0000 | 0.0000 | +0.0000 | 15
answerable_refusal | 0.0000 | 0.0000 | +0.0000 | 15

Positive timing deltas mean slower. Fractions are not percent points. Single-pass uncontrolled comparisons are descriptive, not causal.
Quality comparable: False; full-pipeline timing comparable: True.

### Per-question quality

Case | Previous correctness | Current correctness | Previous faithfulness | Current faithfulness
--- | --- | --- | --- | ---
policy-ai-impersonation | 1.0000 | unavailable | 1.0000 | unavailable
policy-off-campus | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-credits | 1.0000 | 1.0000 | 0.9286 | 1.0000
msds-gpa | 1.0000 | 1.0000 | 0.8000 | 0.8000
msds-waiver | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-industry | 1.0000 | 1.0000 | 1.0000 | 1.0000
missing-personal-schedule | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-admissions-prerequisites | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-working-enrollment | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-pathbreaker-fall2027 | 1.0000 | 1.0000 | 1.0000 | 1.0000
msds-cpt-source-context | 1.0000 | 1.0000 | 1.0000 | 1.0000
missing-exact-tuition-bill | 1.0000 | 0.5000 | 1.0000 | 1.0000
api-setup | 0.8333 | 0.8333 | 1.0000 | 1.0000
api-model-mapping | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-top-p | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-thinking | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-images | 1.0000 | 1.0000 | 1.0000 | 1.0000
api-tools | 1.0000 | 1.0000 | 1.0000 | 1.0000

Definitions: [metrics guide](../../metrics.md).
