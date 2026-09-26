# Complete metric inventory

Metric | Value | N / status
--- | --- | ---
recall_at_k | unavailable | No eligible ranking observations.
precision_at_k | unavailable | No eligible ranking observations.
hit_rate_at_k | unavailable | No eligible ranking observations.
mrr_at_k | unavailable | No eligible ranking observations.
ndcg_at_k | unavailable | No eligible ranking observations.
annotated_char_recall | unavailable | No eligible evidence coverage observations.
full_evidence_recall | unavailable | No eligible evidence coverage observations.
answer_correctness | 1.0000 | 1
answer_completeness | 1 | 1
fully_correct_points | 1 | 1
faithfulness | 1 | 1
answer_relevance | 1.0000 | 1
citation_support | 1 | 1
citation_coverage | 1 | 1
appropriate_abstention | 1 | 1
incorrect_abstention | not_applicable | No applicable reviewed observations in this workload.
answerable_refusal | not_applicable | No applicable reviewed observations in this workload.
strict_pass_rate | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
contradicted_claims | unavailable | Support sufficiency reviewed; no independent contradiction taxonomy.
unsupported_claims | 0 | 1
claim_count | 1 | 1
first_delta_seconds | mean=2.098s, p50=2.098s, p95=2.098s | 1
total_seconds | mean=2.893s, p50=2.893s, p95=2.893s | 1
generation_seconds | mean=1.430s, p50=1.430s, p95=1.430s | 1
generation_first_delta_seconds | mean=0.640s, p50=0.640s, p95=0.640s | 1
retrieval_seconds | mean=1.451s, p50=1.451s, p95=1.451s | 1
embedding_seconds | mean=1.372s, p50=1.372s, p95=1.372s | 1
rerank_seconds | not_applicable | Reranking disabled.
packing_seconds | mean=0.052s, p50=0.052s, p95=0.052s | 1
search_fusion_seconds | unavailable | Production service exposes total retrieval, embedding, rerank and packing; search/fusion not independently timed.
reliability | {"attempted": 1, "planned": 1, "success": 1, "errors": 0, "not_attempted": 0, "success_rate": 1.0, "timeouts": 0, "retries": 0} | 1
judge_reliability | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
judge_seconds | not_applicable | No paid judge; use explicit Codex functional_case_pass_rate and source review.
token_usage.ingestion | not_applicable | No calls for this stage; verified closed baseline index reused.
token_usage.query_embedding | {"total_tokens": 28, "prompt_tokens": 28} | 1
token_usage.generation | {"input_tokens": 2234, "output_tokens": 105, "total_tokens": 2339} | 1
token_usage.judge | not_applicable | No calls for this stage; verified closed baseline index reused.
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | [1121] | 1
concurrency_throughput | {"concurrency": 1, "wall_seconds": 2.8948911670595407, "successful_requests_per_second": 0.3454361294748572} | 1
ingestion | not_applicable | No fresh ingestion; source/index hashes and chunk snapshots verified against the baseline.
update_delete | not_applicable | This live pass queries a copied index; lifecycle checks are separate offline records.
model_loading | not_applicable | Local reranking disabled; no local inference model loaded.
personal_error_abstention | 1 | 1
scope_clarification | not_applicable | No applicable reviewed observations in this workload.
functional_case_pass_rate | 1 | 1
english_compliance | 1 | 1
named_source_compliance | 1 | 1
original_rubric_correctness | 1.0000 | 1
scope_seconds | unavailable | No successful timed observations.
attempt_duration_seconds | mean=2.893s, p50=2.893s, p95=2.893s | 1
failed_total_seconds | not_applicable | No failed attempts in this recovery workload.
failed_first_delta_seconds | not_applicable | No failed attempts in this recovery workload.
failed_generation_seconds | not_applicable | No failed attempts in this recovery workload.
failed_generation_first_delta_seconds | not_applicable | No failed attempts in this recovery workload.
missing_generation_usage | 0 | 1
