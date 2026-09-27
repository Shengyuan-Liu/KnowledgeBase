"""Review retained offline evidence and documentation without provider calls."""
from hashlib import sha256
import json
from pathlib import Path
import re
import socket
import subprocess

from record_check import METRICS

directory = Path(__file__).parent
comparison = json.loads((directory / "comparison.json").read_text())
manifest = json.loads((directory / "frozen-manifest.json").read_text())
for hashes in [manifest["inputs"], comparison["frozen_inputs"], comparison["current_code_hashes"]]:
    for name, expected in hashes.items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name
for record in directory.glob("*.json"):
    data = json.loads(record.read_text())
    if "metric_inventory" not in data:
        continue
    assert set(data["metric_inventory"]) == set(METRICS), record
    for metric in data["metric_inventory"].values():
        assert metric["status"] in {"measured", "not_applicable", "unavailable"}
        assert (metric["value"] is not None) == (metric["status"] == "measured")
        if metric["status"] != "measured":
            assert metric["reason"]
for name, passed, skipped in [
    ("generation-tests-2", 12, 0), ("scoped-backend-tests-1", 81, 0),
    ("backend-tests-1", 752, 1), ("frontend-tests-1", 4, 0), ("browser-tests-1", 1, 0),
]:
    record = json.loads((directory / f"{name}.json").read_text())
    assert record["exit_code"] == 0
    assert record["counts"] == dict(passed=passed, skipped=skipped, failed=0, error=0), name
for name in ["frontend-build-1", "comparison-2"]:
    assert json.loads((directory / f"{name}.json").read_text())["exit_code"] == 0
for name in ["generation-tests-1", "comparison-1"]:
    assert json.loads((directory / f"{name}.json").read_text())["exit_code"] != 0
assert len(comparison["packed_contexts"]) == 32
assert len(comparison["replayed_assessments"]) == 3
assert len(comparison["generation_payloads"]) == 6

paths = [Path(p) for p in ["README.md", "docs/README.md", "docs/answer-grounding.md",
    "docs/evidence-sufficiency.md", "docs/v2/README.md"]] + [directory / "README.md"]
links = 0
for path in paths:
    text = path.read_text()
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        assert (path.parent / link.split("#")[0]).exists(), (path, link)
        links += 1
    assert not any(line.endswith(" ") for line in text.splitlines()), path
for port in [8001, 5174]:
    with socket.socket() as connection:
        connection.settimeout(1)
        assert connection.connect_ex(("127.0.0.1", port)) != 0, f"Browser server still listening on {port}"
subprocess.run(["git", "diff", "--check"], check=True)
raw_check = subprocess.run(["git", "diff", "--cached", "--check"], capture_output=True, text=True)
print(raw_check.stdout, end="")
subprocess.run(["git", "diff", "--cached", "--check", "--", ".",
    ":(exclude)evals/check-runs/20260927-citation-context/*.log"], check=True)
assert subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() == "v2"
print(f"Verified frozen/current hashes, complete metric inventories, final checks, retained failures, {links} documentation links, source/document formatting and stopped browser servers. Raw log whitespace is retained unchanged. Codex reviewed the saved assessment screenshot; no live semantic claim is made.")
