"""Calibrate the claim judge on frozen, labeled development regressions."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from time import perf_counter

from openai import OpenAI

from evals import judge, metrics
from evals.evaluate import EVALS, append_jsonl, digest, git_state, identifier, timestamp, write_json
from knowledgebase.config import Settings

CASES = EVALS / "calibration/cases.json"


def check_expectation(case, review):
    """Score frozen labels without treating a failed judge as a detected answer error."""
    if review["status"] != "ok":
        return {"passed": False, "pending": True, "answer_error_detected": None, "mismatches": ["No valid judgment."]}
    assessment = review["assessment"]
    mismatches = []
    by_id = {c["claim_id"]: c for c in review["claims"]}
    error_detected = False if case["category"] == "incorrect" else None
    for unit, expected in case["expected"]["unit_verdicts"].items():
        actual = [c["verdict"] for c in assessment["claims"] if by_id[c["claim_id"]]["unit_id"] == unit]
        if case["category"] == "incorrect" and expected != "supported" and any(v != "supported" for v in actual):
            error_detected = True
        if not actual or (any(v != expected for v in actual) if expected == "supported" else expected not in actual):
            mismatches.append(f"{unit}: expected {expected}, observed {actual}.")
    for field in ("abstains", "appropriate_abstention"):
        if assessment[field] != case["expected"][field]:
            mismatches.append(f"{field}: expected {case['expected'][field]}, observed {assessment[field]}.")
    if case["category"] in {"correct", "refusal"}:
        if any(p["correctness"] != 2 or not p["present"] for p in assessment["points"]):
            mismatches.append("Correct answer/refusal did not receive full expected-point credit.")
        if any(c["verdict"] != "supported" for c in assessment["claims"]):
            mismatches.append("Correct answer/refusal has a rejected factual claim.")
    return {"passed": not mismatches, "pending": False, "answer_error_detected": error_detected, "mismatches": mismatches}


def summarize(cases, reviews, calls, wall_seconds, concurrency):
    answers = [{"case_id": c["id"], "status": "ok", "answer": c["answer"], "sources": c["sources"]} for c in cases]
    summary = metrics.summarize(cases, answers, reviews, {"top_k": 0}, calls)
    entries = summary["metrics"]
    for key in ("recall_at_k", "precision_at_k", "hit_rate_at_k", "mrr_at_k", "ndcg_at_k",
                "annotated_char_recall", "full_evidence_recall", "first_delta_seconds", "total_seconds",
                "generation_seconds", "generation_first_delta_seconds", "retrieval_seconds", "embedding_seconds",
                "rerank_seconds", "packing_seconds", "search_fusion_seconds", "evidence_tokens",
                "concurrency_throughput", "ingestion", "update_delete", "model_loading", "reliability"):
        entries[key] = metrics.missing("Fixed synthetic answers and sources; no RAG generation, retrieval or ingestion executed.", False)
    for stage in ("ingestion", "query_embedding", "generation"):
        entries["token_usage"][stage] = metrics.missing("Judge-only calibration; this provider stage was not run.", False)
    by_id = {r["case_id"]: r for r in reviews}
    checks = [{"case_id": c["id"], "category": c["category"], **check_expectation(c, by_id[c["id"]])} for c in cases]
    entries["calibration_agreement"] = metrics.measured(sum(c["passed"] for c in checks) / len(cases),
        "fraction", len(cases), "Frozen Codex-authored regression labels; pending judgments fail agreement. Not human or held-out accuracy.", "checks.json")
    for category, name in (("correct", "correct_answer_rejection"), ("incorrect", "known_error_miss"), ("refusal", "refusal_mismatch")):
        subset = [c for c in checks if c["category"] == category]
        passed = lambda c: c["answer_error_detected"] if category == "incorrect" else c["passed"]
        entries[name] = metrics.measured({"mismatched": sum(not passed(c) and not c["pending"] for c in subset),
            "pending": sum(c["pending"] for c in subset), "passed": sum(bool(passed(c)) for c in subset)},
            "cases", len(subset), "Pending is separate from a wrong decision; known-error detection accepts either negative support verdict. Exact verdict classification remains in calibration_agreement.", "checks.json")
    stages = ("inventory", "inventory_audit", "assessment") if any("inventory_audit" in r for r in reviews) else ("inventory", "assessment")
    entries["judge_stage_seconds"] = {stage: metrics.timing([r["calls"][i]["seconds"] for r in reviews if len(r["calls"]) > i])
        for i, stage in enumerate(stages)}
    for entry in [entries["judge_seconds"], *entries["judge_stage_seconds"].values()]:
        if entry["status"] == "measured":
            entry.update(artifact="reviews.jsonl", method="All completed attempts, including pending/errors; median P50, nearest-rank P95; excludes worker queue wait.")
    entries["judge_call_reliability"] = metrics.measured({"attempts": len(calls), "success": sum(c["status"] == "ok" for c in calls),
        "errors": sum(c["status"] != "ok" for c in calls), "timeouts": sum("Timeout" in c.get("error_type", "") for c in calls), "retries": 0},
        "calls", len(calls), "API success is distinct from judgment validity and label agreement.", "calls.jsonl")
    entries["judge_throughput"] = metrics.measured({"concurrency": concurrency, "wall_seconds": wall_seconds,
        "valid_reviews_per_second": sum(r["status"] == "ok" for r in reviews) / wall_seconds},
        "reviews/second", len(reviews), "Entire calibration batch including logging; no RAG requests.", "run.json")
    summary["limitations"] = ["Synthetic development regressions with Codex-authored labels; not human annotation or held-out accuracy.",
        "Raw answers, sources and labels are frozen before grading; labels are not sent to the judge.",
        "A single stochastic pass does not establish grader stability. Citation scope remains same-line."]
    return summary, checks


def run(judge_module=judge):
    """The module parameter allows a frozen previous implementation in controlled comparisons."""
    cases = json.loads(CASES.read_text())
    settings = Settings()
    directory = EVALS / "calibration-runs" / (identifier() + "-" + judge_module.PROTOCOL)
    directory.mkdir(parents=True)
    metadata = {"started_at": timestamp(), "protocol": judge_module.PROTOCOL,
        "protocol_sha256": judge_module.protocol_hash(), "git": git_state(),
        "judge_code_sha256": digest(Path(judge_module.__file__).read_bytes()),
        "cases_sha256": digest(CASES.read_bytes()), "model": settings.judge_model,
        "reasoning_effort": settings.judge_reasoning_effort, "timeout_seconds": settings.judge_timeout_seconds,
        "concurrency": settings.judge_concurrency, "max_retries": 0, "status": "running",
        "warmup": "none; provider caches/load uncontrolled", "reviewer": "LLM judge; labels authored by Codex"}
    write_json(directory / "run.json", metadata)
    (directory / "cases.json").write_bytes(CASES.read_bytes())
    (directory / "judge-source.py").write_bytes(Path(judge_module.__file__).read_bytes())
    print(f"Calibration: {directory}", flush=True)
    started, reviews, calls = perf_counter(), [], []
    with OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                timeout=settings.judge_timeout_seconds, max_retries=0) as sdk:
        def assess(case):
            answer = {"case_id": case["id"], "status": "ok", "answer": case["answer"], "sources": case["sources"]}
            return judge_module.review(sdk, settings.judge_model, case, answer,
                reasoning_effort=None if settings.judge_reasoning_effort == "off" else settings.judge_reasoning_effort)
        with ThreadPoolExecutor(max_workers=settings.judge_concurrency) as pool:
            futures = {pool.submit(assess, c): c for c in cases}
            for future in as_completed(futures):
                row = future.result()
                reviews.append(row)
                append_jsonl(directory / "reviews.jsonl", row)
                for call in row["calls"]:
                    item = {"stage": "judge", "case_id": row["case_id"], **call}
                    calls.append(item)
                    append_jsonl(directory / "calls.jsonl", item)
                print(f"{row['case_id']}: {check_expectation(futures[future], row)}", flush=True)
    metadata.update(status="completed", finished_at=timestamp(), wall_seconds=perf_counter() - started)
    write_json(directory / "run.json", metadata)
    summary, checks = summarize(cases, reviews, calls, metadata["wall_seconds"], settings.judge_concurrency)
    write_json(directory / "summary.json", summary)
    write_json(directory / "checks.json", checks)
    lines = ["# Judge calibration", "", *summary["limitations"], "", *metrics.console_lines(summary), ""]
    (directory / "README.md").write_text("\n".join(lines))
    print("\n".join(lines), flush=True)
    return 0 if all(c["passed"] for c in checks) else 1


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    raise SystemExit(run())
