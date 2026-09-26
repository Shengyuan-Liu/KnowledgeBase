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
answer_correctness | 0.8667 | 15
answer_completeness | 1 | 15
fully_correct_points | 0.8333 | 15
faithfulness | 0.7857 | 14
answer_relevance | 0.9667 | 15
citation_support | 0.7857 | 14
citation_coverage | 0.7381 | 14
appropriate_abstention | 1 | 1
incorrect_abstention | 0 | 14
answerable_refusal | 0 | 14
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 5 | 15
unsupported_claims | 6 | 15
claim_count | 29 | 15
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
judge_reliability | {"reviewed": 16, "valid": 15, "invalid_or_error": 1, "pending": 1} | 16
judge_seconds | mean=12.575s, p50=10.236s, p95=23.846s | 16
token_usage.ingestion | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.query_embedding | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.generation | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.judge | {"input_tokens": 75590, "output_tokens": 32400, "total_tokens": 107990} | 48
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
concurrency_throughput | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ingestion | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
update_delete | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
model_loading | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
calibration_agreement | 0.9375 | 16
correct_answer_rejection | {"mismatched": 0, "pending": 0, "passed": 10} | 10
known_error_miss | {"mismatched": 0, "pending": 1, "passed": 4} | 5
refusal_mismatch | {"mismatched": 0, "pending": 0, "passed": 1} | 1
judge_stage_seconds.inventory | mean=3.439s, p50=2.703s, p95=8.934s | 16
judge_stage_seconds.inventory_audit | mean=1.946s, p50=1.713s, p95=5.413s | 16
judge_stage_seconds.assessment | mean=7.186s, p50=4.917s, p95=17.824s | 16
judge_call_reliability | {"attempts": 48, "success": 48, "errors": 0, "timeouts": 0, "retries": 0} | 48
judge_throughput | {"concurrency": 4, "wall_seconds": 59.09332133305725, "valid_reviews_per_second": 0.2538357916194649} | 16
