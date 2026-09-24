# Interrupted or failed evaluation: recovered observations

Offline report recovery after observed optional-category bug; raw answers/reviews and original run metadata unchanged. Original judge protocol and known semantic/validation failures remain; no fresh generation or grading.

Metric | Value | N / status
--- | --- | ---
recall_at_k | 0.7795 | 16
precision_at_k | 0.3500 | 16
hit_rate_at_k | 0.9375 | 16
mrr_at_k | 0.9375 | 16
ndcg_at_k | 0.8336 | 16
annotated_char_recall | 0.9996 | 16
full_evidence_recall | 0.6875 | 16
answer_correctness | 1.0000 | 12
answer_completeness | 1 | 12
fully_correct_points | 1 | 12
faithfulness | 0.9551 | 12
answer_relevance | 1.0000 | 12
citation_support | 0.9694 | 12
citation_coverage | 0.5736 | 12
appropriate_abstention | 1 | 1
incorrect_abstention | 0 | 11
answerable_refusal | 0 | 11
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 0 | 12
unsupported_claims | 6 | 12
claim_count | 167 | 12
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
judge_reliability | {"reviewed": 18, "valid": 12, "invalid_or_error": 6, "pending": 6} | 18
judge_seconds | mean=37.956s, p50=29.707s, p95=88.891s | 18
token_usage.ingestion | {"total_tokens": 26199, "prompt_tokens": 26199} | 17
token_usage.query_embedding | {"total_tokens": 429, "prompt_tokens": 429} | 18
token_usage.generation | {"input_tokens": 61600, "output_tokens": 2992, "total_tokens": 64592} | 18
token_usage.judge | {"input_tokens": 161692, "output_tokens": 132191, "total_tokens": 293883} | 34
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [3098, 3098, 3271, 3655, 3703, 4009, 3800, 3405, 3871, 3778, 3594, 3569, 249, 951, 3176, 1113, 1923, 1518] | 18
concurrency_throughput | unavailable | No comparable RAG batch wall interval recorded.
ingestion | {"seconds": 7.463589709019288, "files": [{"file_name": "anthropic_api.md", "seconds": 0.9733090410009027, "bytes": 5643}, {"file_name": "university-student-conduct-policy.txt", "seconds": 1.1409382920246571, "bytes": 21406}, {"file_name": "student-resources-overview.txt", "seconds": 0.4701649999478832, "bytes": 2275}, {"file_name": "student-career-development-professional-development-overview.txt", "seconds": 0.22576125001069158, "bytes": 2860}, {"file_name": "student-career-development-professional-career-information.txt", "seconds": 0.2248847089940682, "bytes": 873}, {"file_name": "masters-in-data-science-tracks.txt", "seconds": 0.32023266702890396, "bytes": 4055}, {"file_name": "masters-in-data-science-summer-research-initiative.txt", "seconds": 0.27138766599819064, "bytes": 1752}, {"file_name": "masters-in-data-science-overview.txt", "seconds": 0.24094695888925344, "bytes": 2728}, {"file_name": "masters-in-data-science-industry-concentration.txt", "seconds": 0.5179713749093935, "bytes": 3292}, {"file_name": "masters-in-data-science-financial-aid-fellowships.txt", "seconds": 0.32595879200380296, "bytes": 4136}, {"file_name": "masters-in-data-science-faq.txt", "seconds": 0.40631724998820573, "bytes": 15140}, {"file_name": "masters-in-data-science-faq-general.txt", "seconds": 0.34853125002700835, "bytes": 9840}, {"file_name": "masters-in-data-science-capstone.txt", "seconds": 0.4180574589408934, "bytes": 9715}, {"file_name": "masters-in-data-science-admissions-ambassadors.txt", "seconds": 0.27229637501295656, "bytes": 5917}, {"file_name": "data-science-ms-bulletin.txt", "seconds": 0.4132163330214098, "bytes": 11433}, {"file_name": "curriculum.txt", "seconds": 0.3908102500718087, "bytes": 9132}, {"file_name": "admissions-requirements.txt", "seconds": 0.5019137909403071, "bytes": 8202}], "index_bytes": 2402468, "indexed_chunks": 92} | 17
update_delete | not_applicable | Evaluation creates a fresh isolated corpus; update/delete lifecycle is not exercised.
model_loading | 4.2172 | 1
