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
answer_correctness | 0.6250 | 8
answer_completeness | 0.8750 | 8
fully_correct_points | 0.5625 | 8
faithfulness | 0.5278 | 6
answer_relevance | 1.0000 | 8
citation_support | 0.5278 | 6
citation_coverage | 0.5278 | 6
appropriate_abstention | 0.5000 | 2
incorrect_abstention | 0 | 6
answerable_refusal | 0 | 6
strict_pass_rate | unavailable | Run or judgments incomplete; no full-set pass rate.
contradicted_claims | 5 | 8
unsupported_claims | 7 | 8
claim_count | 16 | 8
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
judge_reliability | {"reviewed": 12, "valid": 8, "invalid_or_error": 4, "pending": 4} | 12
judge_seconds | mean=13.059s, p50=12.630s, p95=20.025s | 12
token_usage.ingestion | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.query_embedding | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.generation | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.judge | {"input_tokens": 37929, "output_tokens": 21053, "total_tokens": 58982} | 24
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
concurrency_throughput | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ingestion | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
update_delete | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
model_loading | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
calibration_agreement | 0.5833 | 12
correct_answer_rejection | {"mismatched": 1, "pending": 3, "passed": 2} | 6
known_error_miss | {"mismatched": 0, "pending": 1, "passed": 4} | 5
refusal_mismatch | {"mismatched": 0, "pending": 0, "passed": 1} | 1
judge_stage_seconds.inventory | mean=2.693s, p50=2.491s, p95=4.341s | 12
judge_stage_seconds.assessment | mean=10.362s, p50=10.432s, p95=16.677s | 12
judge_call_reliability | {"attempts": 24, "success": 24, "errors": 0, "timeouts": 0, "retries": 0} | 24
judge_throughput | {"concurrency": 4, "wall_seconds": 44.73293350008316, "valid_reviews_per_second": 0.17883915437795125} | 12
