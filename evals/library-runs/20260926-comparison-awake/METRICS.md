# Complete metric inventory

Metric | Value | N / status
--- | --- | ---
recall_at_k | 1.0000 | 7
precision_at_k | 0.2571 | 7
hit_rate_at_k | 1 | 7
mrr_at_k | 0.8571 | 7
ndcg_at_k | 0.8946 | 7
annotated_char_recall | 1.0000 | 7
full_evidence_recall | 1.0000 | 7
answer_correctness | 1.0000 | 22
answer_completeness | 1 | 22
fully_correct_points | 1.0000 | 22
faithfulness | 1 | 26
answer_relevance | 1.0000 | 11
citation_support | 1 | 26
citation_coverage | 1 | 26
appropriate_abstention | 1 | 4
incorrect_abstention | 0 | 7
answerable_refusal | 0 | 7
strict_pass_rate | not_applicable | No paid judge; use recorded manual functional protocol.
contradicted_claims | unavailable | Support sufficiency recorded; no separate contradiction taxonomy.
unsupported_claims | 0 | 11
claim_count | 26 | 11
first_delta_seconds | mean=1.285s, p50=1.381s, p95=3.596s | 11
total_seconds | mean=1.757s, p50=1.922s, p95=4.016s | 11
generation_seconds | mean=1.622s, p50=1.559s, p95=2.434s | 9
generation_first_delta_seconds | mean=1.050s, p50=1.065s, p95=2.023s | 9
retrieval_seconds | mean=0.424s, p50=0.452s, p95=1.566s | 11
embedding_seconds | mean=0.495s, p50=0.466s, p95=1.495s | 9
rerank_seconds | not_applicable | Local reranking disabled.
packing_seconds | mean=0.008s, p50=0.003s, p95=0.053s | 9
search_fusion_seconds | unavailable | Production service exposes total retrieval, embedding, rerank and packing; search/fusion not independently timed.
reliability | {"attempted": 11, "planned": 11, "success": 11, "errors": 0, "not_attempted": 0, "success_rate": 1.0, "timeouts": 0, "retries": 0} | 11
judge_reliability | not_applicable | No paid judge; use recorded manual functional protocol.
judge_seconds | not_applicable | No paid judge; use recorded manual functional protocol.
token_usage.ingestion | not_applicable | Verified existing index copied; no ingestion calls.
token_usage.query_embedding | {"total_tokens": 289, "prompt_tokens": 289} | 9
token_usage.generation | {"input_tokens": 28843, "output_tokens": 896, "total_tokens": 29739} | 9
token_usage.judge | not_applicable | No judge calls.
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [2262, 2262, 782, 2262, 906, 1042, 1121, 3779, 4095, 0, 0] | 11
concurrency_throughput | {"concurrency": 1, "wall_seconds": 19.34419545903802, "successful_requests_per_second": 0.5686460325162072} | 11
ingestion | not_applicable | No fresh ingestion; unchanged source/index snapshots verified against the baseline.
update_delete | not_applicable | Not exercised by this live query batch; see offline workflow checks.
model_loading | not_applicable | Local reranking disabled; no local inference model loaded.
functional_case_pass_rate | 1 | 11
english_compliance | 1 | 11
named_source_compliance | 1 | 11
personal_error_abstention | 1 | 2
scope_clarification | 1 | 2
original_rubric_correctness | 0.9722 | 18
scope_seconds | mean=0.001s, p50=0.001s, p95=0.001s | 8
generated_service_seconds | mean=2.146s, p50=2.007s, p95=4.016s | 9
generated_service_first_delta_seconds | mean=1.570s, p50=1.526s, p95=3.596s | 9
total_wall_seconds | mean=1.757s, p50=1.922s, p95=4.016s | 11
first_delta_wall_seconds | mean=1.285s, p50=1.381s, p95=3.596s | 11
generation_wall_seconds | mean=1.622s, p50=1.559s, p95=2.434s | 9
generation_first_delta_wall_seconds | mean=1.050s, p50=1.065s, p95=2.023s | 9
stream_open_seconds | mean=0.829s, p50=0.876s, p95=1.747s | 9
stream_open_wall_seconds | mean=0.829s, p50=0.876s, p95=1.747s | 9
max_service_clock_difference | 0.0000 | 11
runtime_warnings | {"unraisable_async_generator_warnings": 1} | 1
