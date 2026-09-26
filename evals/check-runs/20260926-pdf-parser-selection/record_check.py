"""Retain scoped offline checks, including failures, without provider calls."""

from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

DIRECTORY = Path(__file__).parent
METRICS = [
    "Recall@K", "Precision@K", "Hit Rate@K", "MRR", "NDCG@K", "Final evidence coverage",
    "Answer correctness", "Faithfulness", "Answer completeness", "Answer relevance",
    "Citation support", "Citation coverage", "Abstention", "First-answer-delta latency",
    "Complete-response latency", "Stage latency", "Token usage and cost", "Reliability",
    "Concurrency and throughput", "Ingestion and index",
]

if __name__ == "__main__":
    name, *command = sys.argv[1:]
    target = DIRECTORY / name
    if target.with_suffix(".json").exists():
        raise SystemExit("Use a new record name; results are append-only.")
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], text=True).splitlines()
    hashes = {p: sha256(Path(p).read_bytes()).hexdigest() for p in files
              if Path(p).is_file() and not p.startswith("evals/")}
    started = time.perf_counter()
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + result.stderr
    target.with_suffix(".log").write_text(output)
    record = {
        "command": command, "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "changed_and_tracked_file_hashes": hashes, "device": platform.platform(),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_seconds": time.perf_counter() - started, "exit_code": result.returncode,
        "counts": {s: sum(int(n) for n in re.findall(rf"(\d+) {s}", output))
                   for s in ["passed", "failed", "skipped", "error"]},
        "failures_artifact": target.with_suffix(".log").name,
        "metric_inventory": {m: {
            "status": "not_applicable", "value": None, "unit": None,
            "reason": "Offline adapter/contract checks; no live retrieval, answer, provider, ingestion or load workload.",
            "sample_count": None, "population": "offline tests", "method": "not exercised",
            "aggregation": "none", "artifact": target.with_suffix(".log").name,
        } for m in METRICS},
    }
    target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
    print(output)
    raise SystemExit(result.returncode)
