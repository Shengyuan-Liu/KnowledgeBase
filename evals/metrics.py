"""Metric definitions, explicit missing values, and comparable evaluation summaries."""

import math
import statistics

from evals.evaluate import retrieval_metrics

VERSION = "automated-metrics-v1"


def measured(value, unit, n, method, artifact="answers.jsonl"):
    return {"status": "measured", "value": value, "unit": unit, "n": n,
            "method": method, "artifact": artifact}


def missing(reason, applicable=True):
    return {"status": "unavailable" if applicable else "not_applicable", "value": None, "reason": reason}


def mean(values):
    return statistics.mean(values) if values else None


def timing(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return missing("No successful timed observations.")
    return measured({"mean": mean(values), "p50": statistics.median(values),
                     "p95": values[math.ceil(.95 * len(values)) - 1]}, "seconds", len(values),
                    "Successful observations; median P50, nearest-rank P95.")


def ranking(case, candidates, chunks, k):
    if not case["answerable"]:
        return None
    gold = {c["chunk_id"] for c in chunks if any(
        c["file_name"] == e["file"] and c["start_offset"] < e["end_offset"]
        and c["end_offset"] > e["start_offset"] for e in case["evidence"])}
    if not gold:
        return None
    rel = [int(c["chunk_id"] in gold) for c in candidates[:k]]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rel))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(gold))))
    return {"recall_at_k": sum(rel) / len(gold), "precision_at_k": sum(rel) / k,
            "hit_rate_at_k": int(any(rel)), "mrr_at_k": next((1 / (i + 1) for i, r in enumerate(rel) if r), 0),
            "ndcg_at_k": dcg / ideal, "gold_overlap_ids": sorted(gold), "relevance": rel, "k": k}


def quality(review, case):
    if not review or review["status"] != "ok":
        return None
    a = review["assessment"]
    claims, points = a["claims"], a["points"]
    citations = [c for claim in claims for c in claim["citations"] if c["verdict"] != "not_associated"]
    result = {
        "answer_correctness": mean([p["correctness"] / 2 for p in points]),
        "answer_completeness": mean([int(p["present"]) for p in points]),
        "fully_correct_points": mean([int(p["correctness"] == 2) for p in points]),
        "answer_relevance": a["relevance"] / 2,
        "faithfulness": mean([int(c["verdict"] == "supported") for c in claims]),
        "contradicted_claims": sum(c["verdict"] == "contradicted" for c in claims),
        "unsupported_claims": sum(c["verdict"] != "supported" for c in claims),
        "claim_count": len(claims),
        "citation_support": mean([int(c["verdict"] == "supported") for c in citations]),
        "citation_coverage": mean([int(any(c["verdict"] == "supported" for c in claim["citations"])) for claim in claims]),
        "appropriate_abstention": int(a["appropriate_abstention"]) if not case["answerable"] else None,
        "incorrect_abstention": int(a["abstains"] and not a["refusal_justified"]) if case["answerable"] else None,
        "answerable_refusal": int(a["abstains"]) if case["answerable"] else None,
    }
    result["strict_pass"] = (all(p["correctness"] == 2 for p in points)
                             and all(c["verdict"] == "supported" and any(
                                 x["verdict"] == "supported" for x in c["citations"]) for c in claims)
                             and a["relevance"] == 2
                             and (not a["abstains"] if case["answerable"] else a["appropriate_abstention"]))
    return result


QUALITY_METHODS = {
    "answer_correctness": "Expected-point correctness, 0/1/2 normalized, macro-average. Extra claim errors are separate; not overall accuracy.",
    "answer_completeness": "Fraction of expected points attempted, regardless of truth; macro-average.",
    "fully_correct_points": "Fraction of expected points fully correct (2), macro-average.",
    "faithfulness": "Fraction of inventoried factual claims supported by supplied evidence, macro-average over claim-bearing answers.",
    "answer_relevance": "LLM 0 off-topic / 1 partly responsive or extraneous / 2 directly responsive, normalized macro-average.",
    "citation_support": "Fraction of assessed claim-citation pairs with semantic support, macro-average over cited answers.",
    "citation_coverage": "Fraction of factual claims with at least one supporting inline citation, macro-average over claim-bearing answers.",
    "appropriate_abstention": "Appropriate explicit refusal without invented specifics on unanswerable cases.",
    "incorrect_abstention": "Unjustified refusal on answerable cases despite supplied evidence; separate from retrieval-caused refusals.",
    "answerable_refusal": "Any full/partial refusal on answerable cases, including missing retrieved evidence.",
}


def summarize(cases, answers, reviews, metadata, calls):
    by_case = {r["case_id"]: r for r in reviews}
    successful = [a for a in answers if a["status"] == "ok"]
    cases_by_id = {c["id"]: c for c in cases}
    rows = [{"case_id": a["case_id"], "category": cases_by_id[a["case_id"]].get("category", "uncategorized"), "status": a["status"],
             "coverage": a.get("coverage"), "ranking": a.get("ranking"),
             "quality": quality(by_case.get(a["case_id"]), cases_by_id[a["case_id"]])} for a in answers]
    scores = [r["quality"] for r in rows if r["quality"] is not None]
    metrics = {}
    for key in ("recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k"):
        values = [a["ranking"][key] for a in successful if a.get("ranking")]
        metrics[key] = measured(mean(values), "fraction", len(values),
            f"Selected pre-expansion top-{metadata['top_k']} children; binary nonempty gold-span overlap proxy; "
            "labels are NOT exhaustive semantic relevance. Macro-average answerable cases; precision divides by K, misses zero.") if values else missing("No eligible ranking observations.")
    for key in ("annotated_char_recall", "full_evidence_recall"):
        values = [a["coverage"][key] for a in successful if a.get("coverage", {}).get(key) is not None]
        metrics[key] = measured(mean(values), "fraction", len(values),
            "Union of actual supplied source spans; average gold spans per answer then macro-average answerable cases.") if values else missing("No eligible evidence coverage observations.")
    for key, method in QUALITY_METHODS.items():
        values = [s[key] for s in scores if s[key] is not None]
        metrics[key] = measured(mean(values), "fraction", len(values),
                                method + " Valid LLM review subset only; see judge reliability.", "reviews.jsonl") if values else missing("No valid applicable LLM assessments; claim-free/citation-free answers are excluded.")
    complete = len(answers) == len(cases) and len(scores) == len(successful)
    metrics["strict_pass_rate"] = measured(sum(s["strict_pass"] for s in scores) / len(cases), "fraction", len(cases),
        "All points correct, claims supported and cited, relevant, correct refusal behavior; generation errors fail. LLM assessment, not ground truth.",
        "reviews.jsonl") if complete else missing("Run or judgments incomplete; no full-set pass rate.")
    for key in ("contradicted_claims", "unsupported_claims", "claim_count"):
        metrics[key] = measured(sum(s[key] for s in scores), "claims", len(scores), "Total over valid inventoried reviews.", "reviews.jsonl") if scores else missing("No valid claim assessments.")
    for key in ("first_delta_seconds", "total_seconds", "generation_seconds", "generation_first_delta_seconds",
                "retrieval_seconds", "embedding_seconds", "rerank_seconds", "packing_seconds"):
        metrics[key] = timing([a.get(key) for a in successful])
    metrics["search_fusion_seconds"] = missing("Production service exposes total retrieval, embedding, rerank and packing; search/fusion not independently timed.")
    metrics["reliability"] = measured({"attempted": len(answers), "planned": len(cases), "success": len(successful),
        "errors": len(answers) - len(successful), "not_attempted": len(cases) - len(answers),
        "success_rate": len(successful) / len(cases),
        "timeouts": sum("Timeout" in a.get("error_type", "") for a in answers), "retries": 0},
        "requests", len(answers), "All planned RAG requests; SDK retries disabled, partial answers do not succeed.")
    metrics["judge_reliability"] = measured({"reviewed": len(reviews), "valid": len(scores),
        "invalid_or_error": len(reviews) - len(scores), "pending": len(successful) - len(scores)},
        "reviews", len(reviews), "No automatic repair/retry. Invalid review remains pending; protocol defines judgment stages.", "reviews.jsonl")
    metrics["judge_seconds"] = timing([r["seconds"] for r in reviews])
    if metrics["judge_seconds"]["status"] == "measured":
        metrics["judge_seconds"].update(artifact="reviews.jsonl",
            method="All completed review attempts, including pending/errors; median P50, nearest-rank P95; excludes worker queue wait.")
    usage = {}
    for stage in ("ingestion", "query_embedding", "generation", "judge"):
        observed = [c for c in calls if c.get("stage") == stage]
        usages = [c["usage"] for c in observed if c.get("usage")]
        totals = {key: sum(u[key] for u in usages if key in u) for key in ("input_tokens", "output_tokens", "total_tokens", "prompt_tokens") if any(key in u for u in usages)}
        usage[stage] = measured(totals, "tokens", len(usages),
            f"Provider-reported totals for {len(usages)}/{len(observed)} calls; missing failed-call usage excluded, not zero billed cost.", "calls.jsonl") if usages else missing("No provider usage recorded for this stage.")
    metrics["token_usage"] = usage
    metrics["cost"] = missing("Provider responses do not expose billed dollars; no inferred price substituted.")
    metrics["evidence_tokens"] = measured([a.get("retrieval", {}).get("evidence_tokens") for a in successful], "tokens", len(successful), "Exact formatted supplied evidence tokens including metadata.")
    duration = metadata.get("rag_wall_seconds")
    metrics["concurrency_throughput"] = measured({"concurrency": 1, "wall_seconds": duration,
        "successful_requests_per_second": len(successful) / duration}, "requests/second", len(successful),
        "Sequential RAG batch including logging, excluding initialization, ingestion and judge; not load capacity.") if duration else missing("No comparable RAG batch wall interval recorded.")
    metrics["ingestion"] = measured(metadata["ingestion"], "seconds/bytes/counts", len(metadata["ingestion"]["files"]),
        "Fresh isolated corpus upload to searchable; on-disk index size before queries.", "run.json") if metadata.get("ingestion") else missing("Historical generation replay did not ingest documents.", False)
    metrics["update_delete"] = missing("Evaluation creates a fresh isolated corpus; update/delete lifecycle is not exercised.", False)
    metrics["model_loading"] = measured(metadata["model_load_seconds"], "seconds", 1,
        "Local reranker constructor; excluded from request timings.", "run.json") if "model_load_seconds" in metadata else missing("Model loading not recorded.")
    return {"version": VERSION, "metrics": metrics, "cases": rows,
            "limitations": ["Development/regression set; not held-out accuracy.",
                "LLM judgments are assessments, not human ground truth; inventory misclassification and semantic errors remain possible.",
                "In-process production streaming service, excluding app HTTP transport; no warmup, caches and host/provider load uncontrolled."]}


def compare(before, after, *, quality_compatible, timing_compatible, ranking_compatible=True, same_judge_protocol=False):
    differences = {}
    for key, current in after["metrics"].items():
        old = before["metrics"].get(key, {})
        if key in QUALITY_METHODS or key in ("strict_pass_rate", "contradicted_claims", "unsupported_claims", "claim_count"):
            allowed = quality_compatible and old.get("n") == current.get("n")
        elif key in ("recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k"):
            allowed = ranking_compatible
        elif key in ("first_delta_seconds", "total_seconds", "retrieval_seconds", "embedding_seconds"):
            allowed = timing_compatible
        else:
            allowed = True
        if allowed and old.get("status") == current.get("status") == "measured":
            a, b = old["value"], current["value"]
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                differences[key] = {"before": a, "after": b, "delta": b - a}
            elif isinstance(a, dict) and set(a) == {"mean", "p50", "p95"} and isinstance(b, dict):
                differences[key] = {"before": a, "after": b, "delta": {k: b[k] - a[k] for k in a}}
    old_cases = {r["case_id"]: r for r in before["cases"]}
    pairs = [{"case_id": r["case_id"], "before": old_cases.get(r["case_id"]), "after": r} for r in after["cases"]]
    paired_quality = {}
    if same_judge_protocol:
        valid_pairs = [(r["before"]["quality"], r["after"]["quality"]) for r in pairs
                       if r["before"] and r["before"].get("quality") is not None and r["after"].get("quality") is not None]
        for key in QUALITY_METHODS:
            values = [(a[key], b[key]) for a, b in valid_pairs if a[key] is not None and b[key] is not None]
            if values:
                a, b = mean([v[0] for v in values]), mean([v[1] for v in values])
                paired_quality[key] = {"before": a, "after": b, "delta": b - a, "n": len(values)}
    return {"deltas": differences, "paired_quality": paired_quality,
            "paired_quality_scope": "Only identical case IDs with valid applicable reviews on BOTH sides under the same judge protocol; failures excluded, selection bias possible. Not a full-set comparison.",
            "cases": pairs, "quality_compatible": quality_compatible,
            "end_to_end_timing_compatible": timing_compatible, "ranking_compatible": ranking_compatible,
            "note": "Positive timing deltas mean slower. Fractions are not percent points. Single-pass uncontrolled comparisons are descriptive, not causal."}


def console_lines(summary):
    lines = ["Metric | Value | N / status", "--- | --- | ---"]
    def emit(name, entry):
        if "status" not in entry:
            for key, item in entry.items():
                emit(f"{name}.{key}", item)
        elif entry["status"] != "measured":
            lines.append(f"{name} | {entry['status']} | {entry['reason']}")
        else:
            value = entry["value"]
            if isinstance(value, float):
                text = f"{value:.4f}"
            elif isinstance(value, dict) and set(value) == {"mean", "p50", "p95"}:
                text = ", ".join(f"{k}={v:.3f}s" for k, v in value.items())
            else:
                import json
                text = json.dumps(value, ensure_ascii=False)
            lines.append(f"{name} | {text} | {entry['n']}")
    for name, entry in summary["metrics"].items():
        emit(name, entry)
    return lines
