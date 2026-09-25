"""Record one real-provider UI acceptance attempt in a new isolated directory."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

from evals import metrics
from evals.evaluate import digest, git_state, timestamp, write_json
from knowledgebase.config import Settings

run_id = sys.argv[1]
directory = Path("evals/browser-runs") / run_id
directory.mkdir()
command = ["npx", "playwright", "test", "--config", "playwright.semantic.config.ts"]
overrides = {"LIVE_RUN_ID": run_id, "CHUNKING_STRATEGY": "semantic", "RERANK_ENABLED": "true",
    "OPENAI_MAX_RETRIES": "0", "DATA_DIR": str((Path("data/live-browser") / run_id).resolve())}
env = {**os.environ, **overrides}
settings = Settings(chunking_strategy="semantic", rerank_enabled=True, openai_max_retries=0, data_dir=overrides["DATA_DIR"])
state = git_state()
state["browser_code_sha256"] = {str(path): digest(path.read_bytes()) for path in [
    Path("frontend/live/semantic.spec.ts"), Path("frontend/playwright.semantic.config.ts"),
    Path("frontend/playwright.live.config.ts")]}
report = {"started_at": timestamp(), "command": command, "cwd": "frontend", "environment_overrides": overrides,
    "git": state, "settings": settings.model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"}),
    "concurrency": 1, "retries": 0, "status": "running",
    "scope": "Two synthetic live browser questions, follow-up, persisted diagnostics and source-line fidelity, refresh and deletion. Not an accuracy benchmark."}
write_json(directory / "run.json", report)
started = perf_counter()
result = subprocess.run(command, cwd="frontend", env=env, capture_output=True, text=True)
elapsed = perf_counter() - started
output = result.stdout + result.stderr
(directory / "browser.log").write_text(output)
report.update(finished_at=timestamp(), duration_seconds=elapsed, exit_code=result.returncode,
    counts={status: int(count) for count, status in re.findall(r"(\d+) (passed|failed|skipped)", output)},
    status="passed" if result.returncode == 0 else "failed")
template = json.loads((Path(__file__).parent / "parent_child/summary-all.json").read_text())["metrics"]
inventory = {name: metrics.missing("Live UI smoke test does not provide a frozen relevance inventory or scored claim review; see acceptance.json for saved evidence and assertions.") for name in template}
for name in ("judge_reliability", "judge_seconds", "appropriate_abstention", "incorrect_abstention", "answerable_refusal"):
    inventory[name] = metrics.missing("No automated judge or abstention cases in this two-question UI workflow.", False)
for name in ("first_delta_seconds", "generation_seconds", "generation_first_delta_seconds", "total_seconds"):
    inventory[name] = metrics.missing("Browser records submit-to-Completed UI latency; transport first delta and precise HTTP completion are not instrumented.")
inventory["cost"] = metrics.missing("Production UI does not expose provider billed dollars.")
inventory["token_usage"] = metrics.missing("Production UI does not expose provider token usage; separate paired experiment records provider usage.")
inventory["search_fusion_seconds"] = metrics.missing("No independent search/fusion timer.")
inventory["model_loading"] = metrics.missing("Server startup includes model loading; no separate startup timer in browser test.")
inventory["concurrency_throughput"] = metrics.missing("Single sequential browser workflow includes inspection and deletion, not a request throughput interval.")
inventory["reliability"] = metrics.measured(report["counts"], "browser tests", 1, "One attempt, no retries. Assertions include upload, two answers, restoration and deletion.", "browser.log")
if (directory / "acceptance.json").exists():
    acceptance = json.loads((directory / "acceptance.json").read_text())
    answers = acceptance["answers"]
    inventory["ui_complete_seconds"] = metrics.timing([a["ui_complete_ms"] / 1000 for a in answers])
    inventory["ui_complete_seconds"].update(artifact="acceptance.json", scope="Composer fill/submit to visible Completed; includes browser polling, excludes subsequent history fetch. Not HTTP completion.")
    for name in ("retrieval_seconds", "embedding_seconds", "rerank_seconds", "packing_seconds"):
        inventory[name] = metrics.timing([a["saved"]["messages"][-1]["retrieval"].get(name) for a in answers])
        inventory[name]["artifact"] = "acceptance.json"
    inventory["evidence_tokens"] = metrics.measured([a["saved"]["messages"][-1]["retrieval"]["evidence_tokens"] for a in answers], "tokens", len(answers), "Recorded supplied evidence, including formatting.", "acceptance.json")
    uploaded = [s["details"]["elapsed_ms"] / 1000 for s in acceptance["steps"] if s["name"] == "upload-ready"]
    inventory["ingestion"] = metrics.timing(uploaded)
    inventory["ingestion"].update(artifact="acceptance.json", scope="File input through visible ready notification; one synthetic Markdown file.")
    inventory["update_delete"] = metrics.measured({"delete_verified": any(s["name"] == "deletion-retains-historical-evidence" for s in acceptance["steps"]), "update": "not_applicable; no document update endpoint exercised"}, "checks", 1, "SQLite source/parent/child/indexing records and file list empty; historical sources and diagnostics retained.", "acceptance.json")
    inventory["index_bytes"] = metrics.missing("On-disk bytes before deletion were not measured; exact stored rows are retained.")
report["metric_inventory"] = inventory
write_json(directory / "run.json", report)
print(output)
raise SystemExit(result.returncode)
