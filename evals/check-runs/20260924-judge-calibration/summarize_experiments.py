"""Append an audited comparison of preserved judge-calibration experiments."""

import json
from pathlib import Path

from evals import calibrate, metrics
from evals.evaluate import EVALS, digest, read_jsonl, write_json

CHECKS = Path(__file__).parent
BASELINE = EVALS / "calibration-runs/20260924T191250Z-6825dccf-claim-inventory-v4"
SELECTED = EVALS / "calibration-runs/20260924T193931Z-14f32e71-claim-inventory-v10"
ORIGINAL = EVALS / "runs/20260924T161009Z-f2950a8f-automatic"
FINAL = EVALS / "calibration-runs/20260924T194004Z-1a80463c-saved-answers-high"


def read(path):
    return json.loads(path.read_text())


def review_stats(directory, prefix=""):
    rows = read_jsonl(directory / f"{prefix}reviews.jsonl")
    calls = [c for r in rows for c in r["calls"]]
    usage = [c["usage"] for c in calls if c.get("usage")]
    three_stages = any("inventory_audit" in r for r in rows)
    names = ("inventory", "inventory_audit", "assessment") if three_stages else ("inventory", "assessment")
    return {"attempted": len(rows), "valid": sum(r["status"] == "ok" for r in rows),
        "pending": [{"case_id": r["case_id"], "issues": r.get("inventory_audit", {}),
                     "reason": r.get("validation_error", r.get("error_type"))} for r in rows if r["status"] != "ok"],
        "seconds": metrics.timing([r["seconds"] for r in rows])["value"],
        "stage_seconds": {name: metrics.timing([r["calls"][i]["seconds"] for r in rows if len(r["calls"]) > i])["value"] for i, name in enumerate(names)},
        "calls": len(calls), "usage_observed_calls": len(usage),
        "usage": {key: sum(u[key] for u in usage) for key in ("input_tokens", "output_tokens", "total_tokens")},
        "api_errors": sum(c["status"] != "ok" for c in calls),
        "timeouts": sum("Timeout" in c.get("error_type", "") for c in calls), "retries": 0,
        "method": "All completed attempts including pending/errors; P50 median, P95 nearest rank; no worker queue time.",
        "artifact": str(directory / f"{prefix}reviews.jsonl")}


def main():
    runs = []
    for directory in sorted((EVALS / "calibration-runs").glob("*-claim-inventory-v*")):
        cases, meta = read(directory / "cases.json"), read(directory / "run.json")
        summary, checks = calibrate.summarize(cases, read_jsonl(directory / "reviews.jsonl"),
            read_jsonl(directory / "calls.jsonl"), meta["wall_seconds"], meta["concurrency"])
        for entry in summary["metrics"].values():
            if isinstance(entry, dict) and entry.get("artifact") == "checks.json":
                entry["artifact"] = "checks-audited.json"
        if not (directory / "summary-audited.json").exists():
            write_json(directory / "summary-audited.json", summary)
            write_json(directory / "checks-audited.json", checks)
        runs.append({"run": directory.name, "protocol": meta["protocol"], "reasoning": meta["reasoning_effort"],
            "dataset": cases[0].get("dataset_version", "calibration-v1"), "n": len(cases),
            "agreement": sum(c["passed"] for c in checks), "stats": review_stats(directory)})

    old_cases = {c["id"]: {k: v for k, v in c.items() if k != "dataset_version"} for c in read(BASELINE / "cases.json")}
    new_cases = {c["id"]: {k: v for k, v in c.items() if k != "dataset_version"} for c in read(SELECTED / "cases.json")}
    assert all(new_cases[k] == v for k, v in old_cases.items())
    selected_checks = read(SELECTED / "checks-audited.json")
    write_json(CHECKS / "experiment-comparison-final.json", {"calibration_runs": runs,
        "matched_calibration": {"case_ids": list(old_cases), "before": sum(c["passed"] for c in read(BASELINE / "checks-audited.json")),
            "after": sum(c["passed"] for c in selected_checks if c["case_id"] in old_cases), "n": len(old_cases),
            "caveat": "Prompts, stage count and reasoning effort changed. Do not attribute the improvement to one change."},
        "original_saved_answers": review_stats(ORIGINAL), "final_saved_answers": review_stats(FINAL),
        "same_answer_bytes": (ORIGINAL / "answers.jsonl").read_bytes() == (FINAL / "answers.jsonl").read_bytes(),
        "answer_sha256": digest((FINAL / "answers.jsonl").read_bytes()),
        "cost": metrics.missing("Billed dollars are not exposed by provider responses."),
        "limits": ["Codex-authored synthetic labels, not human ground truth or held-out accuracy.",
            "Some batches overlapped in wall time; each batch used four workers, combined concurrency could reach eight.",
            "Scores change on identical answers: they measure judge changes/variance, not RAG improvement.",
            "Early summaries remain unchanged; audited summaries correct negative-verdict subclassification versus error detection and timing artifact references."]})

    old_reviews = {r["case_id"]: r for r in read_jsonl(ORIGINAL / "reviews.jsonl")}
    comparisons = []
    for review in read_jsonl(FINAL / "reviews.jsonl"):
        claims = {c["claim_id"]: c for c in review.get("claims", [])}
        old = old_reviews[review["case_id"]]
        comparisons.append({"case_id": review["case_id"], "before_status": old["status"], "after_status": review["status"],
            "inventory_audit": review.get("inventory_audit"), "claims": review.get("claims"),
            "negative_claims": [{"extraction": claims[c["claim_id"]], "assessment": c} for c in review.get("assessment", {}).get("claims", []) if c["verdict"] != "supported"]})
    write_json(CHECKS / "saved-answer-inspection-final.json", {"reviewer": "Codex development inspection; not an independent human", "cases": comparisons})


if __name__ == "__main__":
    main()
