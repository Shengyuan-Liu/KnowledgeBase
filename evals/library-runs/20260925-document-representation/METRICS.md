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
answer_correctness | 0.9318 | 22
answer_completeness | 0.9545 | 22
fully_correct_points | 0.9091 | 22
faithfulness | 1 | 21
answer_relevance | 1.0000 | 11
citation_support | 1 | 21
citation_coverage | 1 | 21
appropriate_abstention | 0.7500 | 4
incorrect_abstention | 0 | 7
answerable_refusal | 0 | 7
strict_pass_rate | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
contradicted_claims | unavailable | Support sufficiency reviewed; no independent contradiction taxonomy.
unsupported_claims | 0 | 11
claim_count | 21 | 11
first_delta_seconds | mean=5.053s, p50=1.718s, p95=38.993s | 10
total_seconds | mean=10.443s, p50=3.506s, p95=46.242s | 10
generation_seconds | mean=12.531s, p50=3.187s, p95=46.033s | 8
generation_first_delta_seconds | mean=5.798s, p50=1.147s, p95=38.434s | 8
retrieval_seconds | mean=0.413s, p50=0.293s, p95=1.422s | 10
embedding_seconds | mean=0.483s, p50=0.378s, p95=1.346s | 9
rerank_seconds | not_applicable | Reranking disabled.
packing_seconds | mean=0.010s, p50=0.002s, p95=0.057s | 8
search_fusion_seconds | unavailable | Production service exposes total retrieval, embedding, rerank and packing; search/fusion not independently timed.
reliability | {"attempted": 11, "planned": 11, "success": 10, "errors": 1, "not_attempted": 0, "success_rate": 0.9090909090909091, "timeouts": 1, "retries": 0} | 11
judge_reliability | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
judge_seconds | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
token_usage.ingestion | not_applicable | No calls for this stage; verified closed baseline index reused.
token_usage.query_embedding | {"total_tokens": 289, "prompt_tokens": 289} | 9
token_usage.generation | {"input_tokens": 25979, "output_tokens": 617, "total_tokens": 26596} | 8
token_usage.judge | not_applicable | No calls for this stage; verified closed baseline index reused.
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [2262, 2262, 782, 2262, 906, 1042, 3779, 4095, 0, 0] | 10
concurrency_throughput | {"concurrency": 1, "wall_seconds": 166.62610820797272, "successful_requests_per_second": 0.06001460459917001} | 10
ingestion | not_applicable | No fresh ingestion; source/index hashes and chunk snapshots verified against the baseline.
update_delete | not_applicable | This live pass queries a copied index; lifecycle checks are separate offline records.
model_loading | not_applicable | Local reranking disabled; no local inference model loaded.
personal_error_abstention | 0.5000 | 2
scope_clarification | 1 | 2
functional_case_pass_rate | 0.8182 | 11
english_compliance | 1 | 11
named_source_compliance | 1 | 11
original_rubric_correctness | 0.9444 | 18
scope_seconds | mean=0.001s, p50=0.001s, p95=0.001s | 8
attempt_duration_seconds | mean=15.146s, p50=3.896s, p95=62.179s | 11
failed_total_seconds | mean=62.179s, p50=62.179s, p95=62.179s | 1
failed_first_delta_seconds | mean=1.259s, p50=1.259s, p95=1.259s | 1
failed_generation_seconds | mean=61.782s, p50=61.782s, p95=61.782s | 1
failed_generation_first_delta_seconds | mean=0.862s, p50=0.862s, p95=0.862s | 1
missing_generation_usage | unavailable | Failed generation call(s) have no final provider usage: 20260925T211732Z-bb42dca6
