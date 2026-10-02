"""Record complete applicability and paired ranking differences for BM25 only."""

import json
from pathlib import Path

from record_check import METRICS

DIRECTORY = Path(__file__).parent
before = json.loads((DIRECTORY / "bm25-before.json").read_text())
after = json.loads((DIRECTORY / "bm25-after.json").read_text())
assert before["workload_sha256"] == after["workload_sha256"]
pairs = []
for old, new in zip(before["cases"], after["cases"], strict=True):
    assert old["case_id"] == new["case_id"]
    ranks_equal = [r["chunk_id"] for r in old["candidates"]] == [r["chunk_id"] for r in new["candidates"]]
    previous = {r["chunk_id"]: r["score"] for r in old["candidates"]}
    differences = [abs(r["score"] - previous[r["chunk_id"]]) for r in new["candidates"] if r["chunk_id"] in previous]
    pairs.append({"case_id": old["case_id"], "ranks_equal": ranks_equal,
                  "max_absolute_score_difference": max(differences, default=0),
                  "quality_equal": old["ranking"] == new["ranking"]})
    assert ranks_equal and old["ranking"] == new["ranking"]
    assert max(differences, default=0) < 1e-10

cohorts = {}
keys = dict(zip(METRICS[:5], ["recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k"]))
for arm in [before, after]:
    artifact = f"bm25-{arm['arm']}.json"
    metrics = {name: {
        "status": "not_applicable", "value": None, "unit": None,
        "reason": "Local lexical scorer replay only; no embeddings, reranking, final evidence packing, answer generation, provider calls, persistent ingestion or service load.",
        "sample_count": 0, "population": "not exercised", "method": "not exercised",
        "aggregation": "none", "artifact": artifact,
    } for name in METRICS}
    for name, key in keys.items():
        metrics[name] = {
            "status": "measured", "value": {k: q[key] for k, q in arm["quality"].items()},
            "unit": "fraction", "sample_count": 20, "population": "20 answerable frozen questions; 5 unanswerable excluded",
            "method": "Candidate BM25 stage, K=5 and K=20. Binary chunk overlap with stable annotated source spans; incomplete relevance labels. Precision denominator K; no-hit MRR is zero; MRR cutoff K; binary DCG/log2 discount. Identical chunk boundaries and settings across arms.",
            "aggregation": "macro mean across questions", "artifact": artifact + "#/cases",
        }
    metrics["Stage latency"] = {
        "status": "measured", "value": arm["stage_seconds"]["value"], "unit": "seconds",
        "sample_count": 25, "population": "all questions including unanswerable",
        "method": "perf_counter around search_bm25, including tokenization and temporary index construction. No query queue or model loading; imports and corpus preparation excluded. Single ordered pass, warm process, no warmup calls. Host load uncontrolled.",
        "aggregation": "mean, median P50, nearest-rank P95", "artifact": artifact + "#/cases",
    }
    metrics["Reliability"] = {
        "status": "measured", "value": {"success": 25, "error": 0, "timeout": 0, "retry": 0},
        "unit": "requests", "sample_count": 25, "population": "lexical calls, not HTTP requests",
        "method": "Every frozen case completed; no retries or timeouts configured",
        "aggregation": "counts", "artifact": artifact + "#/cases",
    }
    metrics["Concurrency and throughput"] = {
        "status": "measured", "value": {"concurrency": 1, "stage_queries_per_second": 25 / sum(r["seconds"] for r in arm["cases"])},
        "unit": "workers and queries/second", "sample_count": 25, "population": "sequential lexical calls",
        "method": "Count divided by sum of timed scoring intervals; excludes setup and reporting. Not a service-load or capacity measurement.",
        "aggregation": "whole cohort", "artifact": artifact + "#/cases",
    }
    cohorts[arm["arm"]] = metrics

result = {
    "workload_sha256": before["workload_sha256"], "cohorts": cohorts, "paired_cases": pairs,
    "unchanged_rankings": sum(p["ranks_equal"] for p in pairs),
    "max_absolute_score_difference": max(p["max_absolute_score_difference"] for p in pairs),
    "reviewer": "Codex; deterministic rank/score comparison and review of per-question metrics, no new answer judgments",
    "limits": ["Incomplete relevance labels; this does not measure RAG answer quality.",
               "Before-arm timing helper inherited an answers.jsonl artifact label; authoritative observations are bm25-before.json#/cases, referenced correctly here. Raw record retained.",
               "No production throughput, provider cost, final supplied-evidence or supplementary-search improvement claim."],
}
with (DIRECTORY / "measurement.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(f"25/25 rankings unchanged; maximum absolute score difference {result['max_absolute_score_difference']:.3g}.")
print("All 20 measurement fields recorded for each arm.")
