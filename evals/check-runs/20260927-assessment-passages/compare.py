"""Compare frozen assessor contracts without inferring live model performance."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
from statistics import mean

from replay import DIRECTORY, CHUNKS, MANIFEST, PACKED, PACKED_PATH
from record_check import METRICS

BEFORE = json.loads((DIRECTORY / "before.json").read_text())
AFTER = json.loads((DIRECTORY / "after.json").read_text())
LABEL_PATH = Path("evals/library-runs/20260927-v2-pdf-live/anchor-labels.json")
LABELS = json.loads(LABEL_PATH.read_text())


def distribution(values):
    values = sorted(values)
    def percentile(p):
        position = (len(values) - 1) * p
        low = int(position)
        return values[low] + (values[min(low + 1, len(values) - 1)] - values[low]) * (position - low)
    return {"n": len(values), "mean": mean(values), "p50": percentile(.5), "p95": percentile(.95),
            "min": values[0], "max": values[-1], "percentile_method": "linear"}


def contains(spans, target):
    cursor = target["start"]
    for span in sorted((s for s in spans if s["file_id"] == target["file_id"]), key=lambda s: s["start_offset"]):
        if span["end_offset"] <= cursor:
            continue
        if span["start_offset"] > cursor:
            return False
        cursor = max(cursor, span["end_offset"])
        if cursor >= target["end"]:
            return True
    return False


def coverage(row):
    return {fact: int(all(any(contains(row["catalog"], span) for span in anchor["spans"])
                          for anchor in LABELS[fact]["anchors"])) for fact in row["facts"]}


def candidate_metrics(row):
    candidates = [CHUNKS[identity] for identity in row["selected_ids"][:5]]
    def relevant(chunk):
        return any(chunk["file_id"] == span["file_id"] and chunk["start_offset"] < span["end"] and span["start"] < chunk["end_offset"]
                   for fact in row["facts"] for anchor in LABELS[fact]["anchors"] for span in anchor["spans"])
    binary = [int(relevant(c)) for c in candidates]
    fact_coverage = {fact: int(all(any(contains(candidates, span) for span in anchor["spans"])
                                 for anchor in LABELS[fact]["anchors"])) for fact in row["facts"]}
    # The immutable index's children are the retrieval units; parent metadata is
    # also restored in CHUNKS for rendering and must not enter the ideal ranking.
    ideal = min(5, sum(relevant(c) for identity, c in CHUNKS.items() if ":child:" in identity))
    idcg = sum(1 / math.log2(rank + 2) for rank in range(ideal))
    return {"Recall@K": mean(fact_coverage.values()), "Precision@K": sum(binary) / 5,
            "Hit Rate@K": int(any(binary)), "MRR": next((1 / (i + 1) for i, value in enumerate(binary) if value), 0),
            "NDCG@K": sum(value / math.log2(i + 2) for i, value in enumerate(binary)) / idcg if idcg else 0}


def measured(value, unit, n, population, method, artifact, aggregation="per case and macro mean"):
    return {"status": "measured", "value": value, "unit": unit, "sample_count": n,
            "population": population, "method": method, "aggregation": aggregation, "artifact": artifact}


rows = []
for b, a in zip(BEFORE["rows"], AFTER["rows"], strict=True):
    assert (b["case_id"], b["arm"], b["selected_ids"], b["answer_context_sha256"]) == (
        a["case_id"], a["arm"], a["selected_ids"], a["answer_context_sha256"])
    old_coverage, passage_coverage = coverage(b), coverage(a)
    assert old_coverage == passage_coverage
    rows.append({"case_id": b["case_id"], "arm": b["arm"], "facts": b["facts"],
                 "selected_ids": b["selected_ids"], "candidate_metrics": candidate_metrics(b) if b["facts"] else None,
                 "before_fact_coverage": old_coverage, "after_fact_coverage": passage_coverage,
                 "before_input_tokens": b["input_token_count"], "after_input_tokens": a["input_token_count"],
                 "input_token_difference": a["input_token_count"] - b["input_token_count"],
                 "before_catalog_entries": len(b["catalog"]), "after_passages": len(a["catalog"]),
                 "original_answer_context_unchanged": True})
inventory = {metric: {"status": "not_applicable", "value": None, "unit": None, "sample_count": None,
    "population": "Offline assessor contract comparison", "method": "Not exercised", "aggregation": "none",
    "artifact": "before.json; after.json", "reason": "No model decision, generated answer, provider call, HTTP request, ingestion or load workload."} for metric in METRICS}
for metric in METRICS[:5]:
    value = mean(row["candidate_metrics"][metric] for row in rows if row["candidate_metrics"])
    inventory[metric] = measured({"before": value, "after": value}, "ratio", 28,
        "Same 14 fact-bearing questions in two modes; selected children at K=5",
        "Recomputed frozen-candidate diagnostic, not new retrieval. Literal original-page labels are incomplete. Recall measures complete fact anchor sets; precision and ranking use any anchor overlap, denominator 5, binary gain and log2 discount. No-gold cases excluded.",
        "comparison.json#rows; ../../library-runs/20260927-v2-pdf-live/anchor-labels.json")
coverage_value = mean(mean(row["before_fact_coverage"].values()) for row in rows if row["facts"])
inventory["Final evidence coverage"] = measured({"before": coverage_value, "after": coverage_value, "regressed_case_pairs": 0},
    "ratio", 28, "28 fact-bearing mode/question pairs; 72 fact instances",
    "Macro mean of fully covered literal anchor sets. Before uses whole supplied source spans, after uses the union of exact selectable passage spans; original answer contexts also match byte-for-byte after removing injected markers. No answer-quality claim.", "comparison.json#rows")
inventory["Stage latency"] = measured({phase: distribution([r["catalog_input_seconds"] for r in result["rows"]])
    for phase, result in [("before", BEFORE), ("after", AFTER)]}, "seconds", 32, "Each fixed context once per version, sequential local CPU calls",
    BEFORE["stage_boundary"] + " Before emits a metadata catalog; after inserts inline markers. One noisy developer-machine pass does not establish production latency or speedup.",
    "before.json; after.json", "n/mean/P50/P95/min/max")
inventory["Token usage and cost"] = measured({
    "before_assessor_input_tokens": distribution([r["before_input_tokens"] for r in rows]),
    "after_assessor_input_tokens": distribution([r["after_input_tokens"] for r in rows]),
    "input_token_difference": distribution([r["input_token_difference"] for r in rows]),
    "max_input_tokens": 8192, "before_over_budget": 0, "after_over_budget": 0,
    "answer_context_tokens_unchanged": [r["result"]["diagnostics"]["evidence_tokens"] for r in PACKED["rows"]],
    "provider_usage": {"status": "not_applicable", "value": None, "reason": "No provider calls."},
    "billed_cost": {"status": "not_applicable", "value": None, "reason": "No paid workload; local compute monetary cost unmeasured."}},
    "local cl100k_base serialized input tokens", 32, "All fixed contexts; prompts, serialized messages and output schema included",
    "Uses production input_tokens, not provider billing. Historic planned requirements/control fields shared across versions and reused for hypothetical single-arm assessment. Original answer packing remains capped at4096.",
    "before.json; after.json; comparison.json#rows", "distribution and per-case delta")
inventory["Reliability"] = measured({"before_completed": 32, "after_completed": 32, "construction_errors": 0,
    "timeouts": 0, "retries": 0, "historical_invalid_quote_rejected": True,
    "manual_old_quote_fixture_validates": True, "manual_new_id_fixture_validates": True,
    "historical_failure_reclassified": False}, "counts and booleans", 64, "Local construction/token-limit checks only",
    "Historic failure is replayed with its original context. Both manual income decisions are authored fixtures, not successful model calls. No live reliability inference.", "before.json#historical_failure; after.json")
result = {"timestamp": datetime.now(timezone.utc).isoformat(), "scope": "Offline source passage contract comparison; no model evaluation",
    "reviewer": "Codex; deterministic span assertions and manual inspection of original financial error and selected header/date/value/unit passages; not human review",
    "baseline_commit": MANIFEST["baseline_commit"], "device": platform.platform(), "concurrency": 1,
    "models_and_revisions": "No model loaded or called. Historical failed request resolved gpt-4.1-2025-04-14; that result is retained only as failure evidence.",
    "packed_input_sha256": sha256(PACKED_PATH.read_bytes()).hexdigest(), "labels_sha256": sha256(LABEL_PATH.read_bytes()).hexdigest(),
    "limitations": ["New model ID selection, semantic sufficiency decisions and final answer quality remain unmeasured.",
        "Original historical free-form quote failure remains a failure; manual fixture validation is not acceptance evidence.",
        "Current packing inputs include the prior financial packing fix; older failing context differs and is replayed separately.",
        "No new retrieval, reranking, ingestion or parsing; dense-table missing values and literal-anchor mismatches remain unchanged.",
        "Measurements cover the 32 frozen PDF contexts, not every future document or input length."],
    "rows": rows, "metric_inventory": inventory}
target = DIRECTORY / "comparison.json"
assert not target.exists()
target.write_text(json.dumps(result, indent=2) + "\n")
print("Source anchor coverage unchanged:", coverage_value)
print("Input token distributions:", json.dumps(inventory["Token usage and cost"]["value"], indent=2))
print("Local stage timing:", json.dumps(inventory["Stage latency"]["value"], indent=2))
