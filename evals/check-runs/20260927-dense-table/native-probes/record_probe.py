"""Record each local native-PDF probe invocation without provider calls."""
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

DIRECTORY = Path(__file__).resolve().parent
METRICS = [
    "Recall@K", "Precision@K", "Hit Rate@K", "MRR", "NDCG@K", "Final evidence coverage",
    "Answer correctness", "Faithfulness", "Answer completeness", "Answer relevance",
    "Citation support", "Citation coverage", "Abstention", "First-answer-delta latency",
    "Complete-response latency", "Stage latency", "Token usage and cost", "Reliability",
    "Concurrency and throughput", "Ingestion and index",
]

name, *command = sys.argv[1:]
target = DIRECTORY / name
if target.with_suffix(".json").exists():
    raise SystemExit("Use a fresh invocation name.")
started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
started = time.perf_counter()
result = subprocess.run(command, capture_output=True, text=True)
duration = time.perf_counter() - started
target.with_suffix(".log").write_text(result.stdout + result.stderr)
source_files = [Path("knowledgebase/rag/pdf.py"), Path("knowledgebase/rag/pdf_models.py"),
                *DIRECTORY.glob("*.py")]
inventory = {metric: {
    "status": "not_applicable", "value": None, "unit": None,
    "reason": "Local native PDF extraction only; no retrieval, answer generation, provider calls, ingestion, index or load workload.",
    "sample_count": None, "population": "native parser probes", "method": "not exercised",
    "aggregation": "none", "artifact": target.with_suffix(".log").name,
} for metric in METRICS}
for metric, value, unit, reason in [
    ("Stage latency", duration, "seconds", "Whole local probe invocation, including interpreter startup and parser imports; per-stage durations are in the experiment summary."),
    ("Reliability", {"attempts": 1, "success": int(result.returncode == 0), "errors": int(result.returncode != 0), "timeouts": 0, "retries": 0}, "invocations", "Observed subprocess exit; individual variants recorded separately."),
    ("Concurrency and throughput", {"concurrency": 1, "completed_invocations_per_second": int(result.returncode == 0) / duration}, "invocations/second", "Single sequential offline invocation, not a capacity or production throughput estimate."),
]:
    inventory[metric].update(status="measured", value=value, unit=unit, reason=reason,
                             sample_count=1, method="perf_counter and subprocess exit status", aggregation="single observation")
record = {
    "purpose": "Explore generic native ruled-table extraction for the observed dense digital-PDF failure.",
    "started_at": started_at, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "command": command, "cwd": str(Path.cwd()),
    "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "git_status": subprocess.check_output(["git", "status", "--short"], text=True),
    "source_sha256": {str(path): sha256(path.read_bytes()).hexdigest() for path in source_files},
    "device": platform.platform(), "machine": platform.machine(), "python": sys.version,
    "environment": {key: os.environ[key] for key in ["UV_CACHE_DIR", "PYTHONPATH", "HF_HUB_OFFLINE", "OMP_NUM_THREADS"] if key in os.environ},
    "cache_and_warmup": "No warmup; local OS cache uncontrolled. No model inference or model loading.",
    "concurrency": 1, "timeout_seconds": None, "retry_count": 0,
    "exit_code": result.returncode, "duration_seconds": duration,
    "test_counts": {"passed": 0, "failed": 0, "skipped": 0, "reason": "Exploratory parser variants, not a unit-test run."},
    "metric_inventory": inventory,
}
target.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
print(result.stdout + result.stderr)
raise SystemExit(result.returncode)
