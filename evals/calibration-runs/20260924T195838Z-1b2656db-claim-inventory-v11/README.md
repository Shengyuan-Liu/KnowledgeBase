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
answer_correctness | 0.7812 | 16
answer_completeness | 0.9375 | 16
fully_correct_points | 0.7188 | 16
faithfulness | 0.7333 | 15
answer_relevance | 1.0000 | 16
citation_support | 0.7333 | 15
citation_coverage | 0.6889 | 15
appropriate_abstention | 0.5000 | 2
incorrect_abstention | 0 | 14
answerable_refusal | 0 | 14
strict_pass_rate | 0.5625 | 16
contradicted_claims | 6 | 16
unsupported_claims | 7 | 16
claim_count | 28 | 16
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
judge_reliability | {"reviewed": 16, "valid": 16, "invalid_or_error": 0, "pending": 0} | 16
judge_seconds | mean=14.170s, p50=12.182s, p95=28.080s | 16
token_usage.ingestion | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.query_embedding | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.generation | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.judge | {"input_tokens": 81862, "output_tokens": 31025, "total_tokens": 112887} | 48
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
concurrency_throughput | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ingestion | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
update_delete | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
model_loading | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
calibration_agreement | 0.9375 | 16
correct_answer_rejection | {"mismatched": 0, "pending": 0, "passed": 10} | 10
known_error_miss | {"mismatched": 0, "pending": 0, "passed": 5} | 5
refusal_mismatch | {"mismatched": 0, "pending": 0, "passed": 1} | 1
judge_stage_seconds.inventory | mean=3.818s, p50=3.369s, p95=10.751s | 16
judge_stage_seconds.inventory_audit | mean=2.429s, p50=1.935s, p95=5.329s | 16
judge_stage_seconds.assessment | mean=7.921s, p50=6.068s, p95=21.883s | 16
judge_call_reliability | {"attempts": 48, "success": 48, "errors": 0, "timeouts": 0, "retries": 0} | 48
judge_throughput | {"concurrency": 4, "wall_seconds": 70.22419054200873, "valid_reviews_per_second": 0.2278417148920878} | 16
