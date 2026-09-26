"""Validate completed acceptance artifacts without making provider requests."""
import json
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

from evals import judge
from evals.evaluate import digest, git_state, read_jsonl, timestamp, write_json
from knowledgebase.config import Settings

DIRECTORY = Path(__file__).parent


def main(name):
    target = DIRECTORY / f"{name}.json"
    if target.exists():
        raise SystemExit("Use a new audit name; previous attempts remain unchanged.")
    started = perf_counter()
    report = {"command": ["uv", "run", "--locked", "python", str(Path(__file__)), name],
        "environment": {"PYTHONPATH": "."}, "started_at": timestamp(), "git": git_state(),
        "checks": [], "status": "running"}

    def check(label, condition):
        report["checks"].append({"name": label, "passed": bool(condition)})
        assert condition, label

    try:
        plan = json.loads((DIRECTORY / "plan.json").read_text())
        check("Judge protocol unchanged", judge.protocol_hash() == plan["judge_protocol_sha256"])
        cases = json.loads((DIRECTORY / "cases.json").read_text())
        check("Frozen questions unchanged", digest(json.dumps(cases, sort_keys=True).encode()) == plan["cases_sha256"])
        comparison = json.loads((DIRECTORY / "comparison.json").read_text())
        check("All parent regions unchanged", comparison["parents_identical"] and comparison["parent_count"] == 38)
        for mode in ("parent_child", "semantic"):
            directory = DIRECTORY / mode
            answers, reviews, calls = (read_jsonl(directory / f"{kind}.jsonl") for kind in ("answers", "reviews", "calls"))
            expected = {c["id"] for c in cases}
            check(f"{mode}: exactly one successful answer and review per frozen case", len(answers) == len(reviews) == 24
                and all({r["case_id"] for r in rows} == expected and all(r["status"] == "ok" for r in rows) for rows in (answers, reviews)))
            check(f"{mode}: every review refers to the exact recorded answer", all(
                r["answer_sha256"] == digest(json.dumps(next(a for a in answers if a["case_id"] == r["case_id"]), sort_keys=True).encode()) for r in reviews))
            check(f"{mode}: every response completed and every provider call succeeded", all(any(e["event"] == "complete" for e in a["events"]) for a in answers)
                and all(c["status"] == "ok" for c in calls))
            summary = json.loads((directory / "summary-all.json").read_text())["metrics"]
            check(f"{mode}: no pending judgments", summary["judge_reliability"]["value"]["pending"] == 0)
            check(f"{mode}: exact source slices represented by recorded parent/child units", all(
                any(s["file_name"] == unit["file_name"] and s["start_offset"] == unit["start_offset"]
                    and s["end_offset"] == unit["end_offset"] and s["text"] == unit["text"]
                    for unit in json.loads((directory / "parents.json").read_text()) + json.loads((directory / "chunks.json").read_text()))
                for a in answers for s in a["sources"]))
        documents = [DIRECTORY / "README.md", DIRECTORY / "REVIEW.md", Path("README.md"),
            Path("docs/semantic-chunking.md"), Path("docs/v1/README.md"), Path("docs/v1/v1-technical-plan.md")]
        for document in documents:
            links = [link.split("#")[0] for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text())
                if not link.startswith(("https:", "http:", "mailto:", "#"))]
            check(f"Local links exist: {document}", all((document.parent / link).exists() for link in links))
        result = subprocess.run(["git", "diff", "--check"], capture_output=True, text=True)
        check("Changed-file whitespace review", result.returncode == 0)
        key = Settings().openai_api_key
        roots = [DIRECTORY, Path("evals/browser-runs/20260925-semantic-ui-1")]
        check("Authorized credential absent from saved artifacts", bool(key) and all(
            key.encode() not in path.read_bytes() for root in roots for path in root.rglob("*") if path.is_file()))
        report.update(status="passed", exit_code=0)
    except Exception as error:
        report.update(status="failed", exit_code=1, error_type=type(error).__name__, error=str(error))
    inventory = json.loads((DIRECTORY / "analysis-check-1.json").read_text())["metric_inventory"]
    report["metric_inventory"] = {key: {"status": "not_applicable", "value": None,
        "reason": "Offline artifact integrity review; no new provider calls, quality assessment or performance workload. Live measurements remain in experiment summaries."} for key in inventory}
    report.update(finished_at=timestamp(), seconds=perf_counter() - started,
        counts={"passed": sum(c["passed"] for c in report["checks"]), "failed": sum(not c["passed"] for c in report["checks"]), "skipped": 0},
        documentation_review="Codex reviewed README/REVIEW claims against recorded answers, excerpts, metrics and screenshots; checked Markdown tables and local links.")
    write_json(target, report)
    print(report["status"], report["counts"], report.get("error", ""))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
