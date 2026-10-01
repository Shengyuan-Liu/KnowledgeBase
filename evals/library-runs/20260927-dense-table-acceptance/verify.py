"""Verify this frozen run's records and documentation without provider calls."""

import ast
from collections import Counter
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import re
import socket
import subprocess

from record_check import METRICS

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
checks = []


def read(name):
    return json.loads((RUN / name).read_text())


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    assert condition, name


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def inventory(name, entries):
    check(name + ": complete metric names", set(entries) == set(METRICS))
    for metric, entry in entries.items():
        check(name + ": " + metric, entry["status"] in {"measured", "not_applicable", "unavailable"}
              and (entry.get("value") is not None if entry["status"] == "measured" else bool(entry.get("reason"))))


assert not (RUN / "verification-details.json").exists(), "Append-only output already exists."
preparation = read("preparation.json")
check("active development branch", subprocess.check_output(
    ["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "v2")
for path, expected in preparation["frozen_inputs"].items():
    check("frozen input: " + Path(path).name, digest(ROOT / path) == expected)
for path, expected in preparation["production_hashes"].items():
    check("unchanged production: " + path, digest(ROOT / path) == expected)
for path, expected in preparation["harness_hashes"].items():
    check("unchanged live harness: " + path, digest(RUN / path) == expected)
check("local environment unchanged", digest(ROOT / ".env") == preparation["env_file_sha256"])

frozen = read("frozen-cases.json")
primary = read("review/reviewed-cases.json")
secondary = read("root-review.json")
review_rows = {(row["case_id"], row["arm"]): row for row in primary["rows"]}
root_rows = {(row["case_id"], row["arm"]): row for row in secondary["rows"]}
expected_ids = {(case["id"], arm) for case in frozen["cases"] for arm in ["single", "planned"]}
check("six unique review identities", set(review_rows) == set(root_rows) == expected_ids and len(expected_ids) == 6)
raw_rows = []
for case in frozen["cases"]:
    for arm in ["single", "planned"]:
        identity = (case["id"], arm)
        raw = read(case["id"] + "-" + arm + ".json")
        raw_rows.append(raw)
        check(str(identity) + ": frozen question", raw["request"]["question"] == case["question"])
        check(str(identity) + ": completed", raw["status"] == "completed" and raw["http_status"] == 200)
        check(str(identity) + ": delta assembly", "".join(event["data"]["delta"] for event in raw["events"]
              if event["data"]["event"] == "answer_delta") == raw["answer"]["answer"])
        check(str(identity) + ": history answer/retrieval", raw["history_matches"] and raw["history_retrieval_matches"])
        saved_sources = raw["saved_message"]["sources"]
        check(str(identity) + ": source history schema extension", all(source.get("file_deleted") is False for source in saved_sources))
        common = [{key: value for key, value in source.items() if key != "file_deleted"} for source in saved_sources]
        check(str(identity) + ": shared source fields", common == raw["answer"]["sources"])
        primary_points = review_rows[identity]["points"]
        root_points = root_rows[identity]["points"]
        check(str(identity) + ": frozen point identities", [point["fact_id"] for point in primary_points] == case["expected_fact_ids"])
        for first, second in zip(primary_points, root_points, strict=True):
            check(str(identity) + ": independent score agreement " + first["fact_id"],
                  all(first[key] == second[key] for key in ["fact_id", "reference_correctness", "completeness", "supplied_evidence_coverage"]))
check("three raw history differences retained", sum(not row["history_sources_match"] for row in raw_rows) == 3)
points = [point for row in primary["rows"] for point in row["points"]]
check("24 points; two correct and complete", len(points) == 24 and
      sum(point["reference_correctness"] == point["completeness"] == 1 for point in points) == 2)

measurement = read("metrics/measurement.json")
check("canonical measurement pointer", read("measurement.json")["artifact"] == "metrics/measurement.json")
for name, entries in measurement["groups"].items():
    inventory("answer metrics: " + name, entries)
inventory("shared preparation", measurement["shared_preparation"])
check("measurement review identity", measurement["validity"]["review_sha256"] == digest(RUN / "review/reviewed-cases.json"))
check("failed semantic gate preserved", not measurement["scoped_gates"]["requested_points_correct_and_complete"]["passed"])
for path in RUN.rglob("*.json"):
    record = json.loads(path.read_text())
    if isinstance(record, dict) and "metric_inventory" in record:
        inventory(str(path.relative_to(RUN)), record["metric_inventory"])

observations = [json.loads(line) for line in (RUN / "server-observations.jsonl").read_text().splitlines()]
starts = [row for row in observations if row["kind"] == "sdk_start"]
terminals = [row for row in observations if row["kind"] in {"sdk_complete", "sdk_stream_terminal"}]
check("19 starts with exact matching terminals", len(starts) == 19 and Counter(row["call_id"] for row in starts) == Counter(row["call_id"] for row in terminals))
check("no SDK errors", not any(row["kind"] == "sdk_error" for row in observations))
check("zero provider retries configured", preparation["provider_retries"] == 0)
check("blank case made no SDK calls", not any(row["request"].startswith("grouped-and-blank-cells") for row in starts))

stop = read("server-stop.json")
check("shutdown record confirms release", stop["port_closed"] and stop["ownership_lock_released"])
with socket.socket() as connection:
    check("evaluation port remains closed", connection.connect_ex(("127.0.0.1", read("server-start.json")["port"])) != 0)
with (Path(preparation["data_directory"]) / ".owner.lock").open("r+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    check("isolated library ownership released", True)
    fcntl.flock(lock, fcntl.LOCK_UN)

for path in RUN.rglob("*.py"):
    ast.parse(path.read_text(), filename=str(path))
    check("evaluation script syntax: " + str(path.relative_to(RUN)), True)
docs = list(RUN.rglob("*.md")) + [ROOT / path for path in ["docs/v2/README.md", "docs/pdf-parsing.md", "docs/pdf-integration.md"]]
pending_record = RUN / "verification-1.json"
for path in docs:
    content = path.read_text()
    check("English documentation: " + str(path.relative_to(ROOT)), not re.search(r"[\u4e00-\u9fff]", content))
    check("balanced code fences: " + str(path.relative_to(ROOT)), content.count("```") % 2 == 0)
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
        if re.match(r"(?:https?://|mailto:|#)", target):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        check("local documentation target: " + str(path.relative_to(ROOT)) + " -> " + target,
              resolved.exists() or resolved == pending_record)
check("working diff whitespace", subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True).returncode == 0)
review = {
    "reviewed_at": datetime.now(timezone.utc).isoformat(),
    "scope": "Frozen run consistency, evaluation script syntax, and documentation content/link/format review; no paid/provider calls or production tests.",
    "content_review": "README reviewed against raw answers, both reviewer records, exact model inputs, diagnostics and complete measurements. Failed acceptance, rubric disagreement, missing billing, blank-cell non-exercise, and limited historical comparison remain explicit.",
    "pending_link": "verification-1.json is the enclosing command record and is written by record_check.py after this script exits.",
    "checks": checks,
    "counts": {"passed": len(checks), "failed": 0, "skipped": 0},
}
(RUN / "verification-details.json").write_text(json.dumps(review, indent=2) + "\n")
print(f"{len(checks)} passed, 0 failed, 0 skipped. Frozen artifacts, full metric inventories, history parity, SDK identity, shutdown, and document links verified.")
