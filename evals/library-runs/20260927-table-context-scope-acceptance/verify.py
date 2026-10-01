"""Verify frozen inputs, complete reporting and final documentation without API calls."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import socket
import subprocess

from record_check import METRICS

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
checks = 0


def read(name):
    return json.loads((RUN / name).read_text())


def check(condition, label):
    global checks
    assert condition, label
    checks += 1


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


preparation = read("preparation.json")
for path, expected in preparation["frozen_inputs"].items():
    check(digest(ROOT / path) == expected, "frozen " + path)
for path, expected in preparation["production_hashes"].items():
    check(digest(ROOT / path) == expected, "unchanged product " + path)
for name, expected in preparation["harness_hashes"].items():
    check(digest(RUN / name) == expected, "unchanged live harness " + name)
check(digest(ROOT / ".env") == preparation["env_file_sha256"], "local environment unchanged")
check(subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "v2", "active branch")

measurement = read("metrics/measurement.json")
check(read("measurement.json")["artifact"] == "metrics/measurement.json", "canonical metric pointer")
for label, inventory in [*measurement["groups"].items(), ("preparation", measurement["shared_preparation"])]:
    check(set(inventory) == set(METRICS), label + " complete 20 metrics")
    for metric, entry in inventory.items():
        check(entry["status"] in {"measured", "not_applicable", "unavailable"}, label + metric)
        check(entry.get("value") is not None if entry["status"] == "measured" else bool(entry.get("reason")), label + metric + " value/reason")
review = read("review/reconciliation.json")
check(not review["disagreements"], "independent agreement")
check(review["primary_sha256"] == digest(RUN / "review/reviewed-cases.json"), "primary review identity")
check(review["secondary_sha256"] == digest(RUN / "root-review.json"), "root review identity")
check(review["result"] == dict(correct_complete_points=19, requested_points=24, supplied_evidence_points=24,
      supported_factual_groups=19, factual_groups=23, incorrect_full_abstentions=0), "semantic failure retained")
check(not measurement["scoped_gates"]["requested_points_correct_and_complete"]["passed"], "failed acceptance gate")
observations = [json.loads(line) for line in (RUN / "server-observations.jsonl").read_text().splitlines()]
starts = [row for row in observations if row["kind"] == "sdk_start"]
terminals = [row for row in observations if row["kind"] in {"sdk_complete", "sdk_stream_terminal"}]
check(len(starts) == 27 and Counter(row["call_id"] for row in starts) == Counter(row["call_id"] for row in terminals), "27 provider calls terminated exactly once")
check(sum(row["input"].get("stream", False) for row in starts) == 6, "six generation streams")
check(not any(row["kind"] == "sdk_error" for row in observations), "no observed provider errors")
check(read("run-integrity.json")["shutdown_verified"], "recorded shutdown")
with socket.socket() as connection:
    check(connection.connect_ex(("127.0.0.1", 8786)) != 0, "evaluation port closed")

docs = list(RUN.rglob("*.md")) + [ROOT / name for name in ["docs/v2/README.md", "docs/pdf-integration.md"]]
for path in docs:
    content = path.read_text()
    check(not re.search(r"[\u4e00-\u9fff]", content), "English " + str(path.relative_to(ROOT)))
    check(content.count("```") % 2 == 0, "code fences " + str(path.relative_to(ROOT)))
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
        if re.match(r"(?:https?://|mailto:|#)", target):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        check(resolved.exists() or resolved == RUN / "verification-1.json", "local link " + target)
patterns = [r"sk-proj-[A-Za-z0-9_-]{20,}", r"sk-[A-Za-z0-9_-]{32,}", r"Bearer [A-Za-z0-9_-]{20,}"]
for path in RUN.rglob("*"):
    if path.is_file() and path.suffix in {".json", ".jsonl", ".log", ".md", ".txt"}:
        text = path.read_text()
        check(not any(re.search(pattern, text) for pattern in patterns), "no credential pattern in " + path.name)
check(subprocess.run(["git", "diff", "--check", "--", "*.py", "*.md", "*.ts", "*.tsx"], capture_output=True).returncode == 0, "code/doc whitespace")
print(f"{checks} passed, 0 failed, 0 skipped. Frozen inputs, provider identities, complete metrics, independent review, credential patterns, final document links and formatting verified.")
print("Raw contexts preserve exact table whitespace. No provider call or live rerun performed. Correctness remains19/24; record validation does not pass semantic acceptance.")
