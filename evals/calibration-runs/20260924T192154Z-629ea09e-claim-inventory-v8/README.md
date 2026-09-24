# Judge calibration

Synthetic development regressions with Codex-authored labels; not human annotation or held-out accuracy.
Raw answers, sources and labels are frozen before grading; labels are not sent to the judge.
A single stochastic pass does not establish grader stability. Citation scope remains same-line.

Metric | Value | N / status
--- | --- | ---
recall_at_k | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
precision_at_k | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
hit_rate_at_k | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
mrr_at_k | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ndcg_at_k | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
annotated_char_recall | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
full_evidence_recall | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
answer_correctness | 0.8077 | 13
answer_completeness | 0.9231 | 13
fully_correct_points | 0.7308 | 13
faithfulness | 0.6667 | 12
answer_relevance | 1.0000 | 13
citation_support | 0.6667 | 12
citation_coverage | 0.6667 | 12
appropriate_abstention | 0.5000 | 2
incorrect_abstention | 0 | 11
answerable_refusal | 0 | 11
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 4 | 13
unsupported_claims | 9 | 13
claim_count | 23 | 13
first_delta_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
total_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
generation_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
generation_first_delta_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
retrieval_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
embedding_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
rerank_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
packing_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
search_fusion_seconds | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
reliability | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
judge_reliability | {"reviewed": 14, "valid": 13, "invalid_or_error": 1, "pending": 1} | 14
judge_seconds | mean=9.747s, p50=8.998s, p95=16.548s | 14
token_usage.ingestion | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.query_embedding | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.generation | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.judge | {"input_tokens": 54750, "output_tokens": 15185, "total_tokens": 69935} | 41
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
concurrency_throughput | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ingestion | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
update_delete | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
model_loading | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
calibration_agreement | 0.8571 | 14
correct_answer_rejection | {"mismatched": 1, "pending": 1, "passed": 6} | 8
known_error_miss | {"mismatched": 0, "pending": 0, "passed": 5} | 5
refusal_mismatch | {"mismatched": 0, "pending": 0, "passed": 1} | 1
judge_stage_seconds.inventory | mean=2.675s, p50=2.424s, p95=5.213s | 14
judge_stage_seconds.inventory_audit | mean=1.952s, p50=1.490s, p95=5.343s | 14
judge_stage_seconds.assessment | mean=5.510s, p50=4.558s, p95=10.437s | 13
judge_call_reliability | {"attempts": 41, "success": 41, "errors": 0, "timeouts": 0, "retries": 0} | 41
judge_throughput | {"concurrency": 4, "wall_seconds": 38.78026437503286, "valid_reviews_per_second": 0.33522205713402864} | 14
