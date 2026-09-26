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
answer_correctness | 0.7857 | 14
answer_completeness | 0.9286 | 14
fully_correct_points | 0.7500 | 14
faithfulness | 0.6538 | 13
answer_relevance | 1.0000 | 14
citation_support | 0.6923 | 13
citation_coverage | 0.6538 | 13
appropriate_abstention | 0.5000 | 2
incorrect_abstention | 0 | 12
answerable_refusal | 0 | 12
strict_pass_rate | 0.5714 | 14
contradicted_claims | 4 | 14
unsupported_claims | 10 | 14
claim_count | 27 | 14
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
judge_reliability | {"reviewed": 14, "valid": 14, "invalid_or_error": 0, "pending": 0} | 14
judge_seconds | mean=10.587s, p50=10.227s, p95=20.896s | 14
token_usage.ingestion | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.query_embedding | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.generation | not_applicable | Judge-only calibration; this provider stage was not run.
token_usage.judge | {"input_tokens": 60475, "output_tokens": 16616, "total_tokens": 77091} | 42
cost | unavailable | Provider responses do not expose billed dollars; no inferred price substituted.
evidence_tokens | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
concurrency_throughput | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
ingestion | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
update_delete | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
model_loading | not_applicable | Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.
calibration_agreement | 0.9286 | 14
correct_answer_rejection | {"mismatched": 1, "pending": 0, "passed": 7} | 8
known_error_miss | {"mismatched": 0, "pending": 0, "passed": 5} | 5
refusal_mismatch | {"mismatched": 0, "pending": 0, "passed": 1} | 1
judge_stage_seconds.inventory | mean=3.148s, p50=2.714s, p95=5.640s | 14
judge_stage_seconds.inventory_audit | mean=1.688s, p50=1.460s, p95=3.296s | 14
judge_stage_seconds.assessment | mean=5.749s, p50=4.614s, p95=17.040s | 14
judge_call_reliability | {"attempts": 42, "success": 42, "errors": 0, "timeouts": 0, "retries": 0} | 42
judge_throughput | {"concurrency": 4, "wall_seconds": 41.34154016699176, "valid_reviews_per_second": 0.33864243914110365} | 14
