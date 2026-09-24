# Interrupted evaluation

Interrupted protocol-3 grading. RAG observations were copied from 20260924T154305Z-4ef1ccf3-automatic, not newly executed. Raw records and original run metadata retained unchanged.

Metric | Value | N / status
--- | --- | ---
recall_at_k | 0.7795 | 16
precision_at_k | 0.3500 | 16
hit_rate_at_k | 0.9375 | 16
mrr_at_k | 0.9375 | 16
ndcg_at_k | 0.8336 | 16
annotated_char_recall | 0.9996 | 16
full_evidence_recall | 0.6875 | 16
answer_correctness | 1.0000 | 5
answer_completeness | 1 | 5
fully_correct_points | 1 | 5
faithfulness | 0.9580 | 5
answer_relevance | 1.0000 | 5
citation_support | 0.9889 | 5
citation_coverage | 0.3966 | 5
appropriate_abstention | unavailable | No valid applicable LLM assessments; claim-free/citation-free answers are excluded.
incorrect_abstention | 0 | 5
answerable_refusal | 0 | 5
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 0 | 5
unsupported_claims | 2 | 5
claim_count | 54 | 5
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
judge_reliability | {"reviewed": 5, "valid": 5, "invalid_or_error": 0, "pending": 13} | 5
judge_seconds | mean=35.954s, p50=28.710s, p95=65.537s | 5
token_usage.ingestion | {"total_tokens": 26199, "prompt_tokens": 26199} | 17
token_usage.query_embedding | {"total_tokens": 429, "prompt_tokens": 429} | 18
token_usage.generation | {"input_tokens": 61600, "output_tokens": 2992, "total_tokens": 64592} | 18
token_usage.judge | {"input_tokens": 59385, "output_tokens": 34278, "total_tokens": 93663} | 10
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [3098, 3098, 3271, 3655, 3703, 4009, 3800, 3405, 3871, 3778, 3594, 3569, 249, 951, 3176, 1113, 1923, 1518] | 18
concurrency_throughput | unavailable | No comparable RAG batch wall interval recorded.
ingestion | not_applicable | Historical generation replay did not ingest documents.
update_delete | not_applicable | Evaluation creates a fresh isolated corpus; update/delete lifecycle is not exercised.
model_loading | unavailable | Model loading not recorded.
