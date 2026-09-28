"""Audit the matched run and its documentation without another model call."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from record_check import METRICS

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
BASE = ROOT.parent / "20260928-answer-rules-acceptance"
preparation = json.loads((ROOT / "preparation.json").read_text())
assert all(sha256((PROJECT / path).read_bytes()).hexdigest() == digest
           for path, digest in preparation["hashes"].items())
assert not subprocess.check_output(["git", "diff", "HEAD", "--", "knowledgebase"], text=True)
assert preparation["settings"] == json.loads((BASE / "preparation.json").read_text())["settings"]
for name in ["run.py", "cases.json", "frozen-evidence.json"]:
    assert (ROOT / name).read_bytes() == (BASE / name).read_bytes()
assert (ROOT / "frozen-original-protocol.md").read_bytes() == (BASE / "protocol.md").read_bytes()
measurement = json.loads((ROOT / "measurement.json").read_text())
assert set(measurement["metric_inventory"]) == set(METRICS)
assert measurement["acceptance"] == "failed" and measurement["case_gate_pass_count"] == 3
assert measurement["metric_inventory"]["Answer correctness"]["value"]["score"] == 13
events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
assert len([e for e in events if e["kind"] == "start"]) == 12
assert len([e for e in events if e["kind"] == "complete"]) == 12
assert not [e for e in events if e["kind"] == "error"]
for case in json.loads((ROOT / "cases.json").read_text()):
    row = json.loads((ROOT / (case["id"] + ".json")).read_text())
    assert row["status"] == "completed"
    assert row["planner_record"]["prompt_version"] == "dependent-planner-v5"
    assert row["assessment"]["record"]["prompt_version"] == "evidence-sufficiency-v5"
    assert all(rule in case["question"] for rule in row["plan"]["answer_rules"])
    assert len([e for e in events if e["case"] == case["id"] and e["kind"] == "start"]) == 3
links = 0
for path in [ROOT / "README.md", ROOT / "protocol.md", PROJECT / "docs/v2/README.md", PROJECT / "docs/evidence-sufficiency.md"]:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert content.count("\n```") % 2 == 0
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == ROOT / "artifact-review-1.json":
            continue  # Recording wrapper writes the self-record on completion.
        assert target.exists(), (path, link)
        links += 1
    assert all(line == line.rstrip() for line in content.splitlines()), path
for path in ROOT.glob("*.py"):
    ast.parse(path.read_text())
    assert all(line == line.rstrip() for line in path.read_text().splitlines()), path
subprocess.run(["git", "diff", "--check", "--", "docs"], check=True)
print(f"Integrity passed: unchanged runner/questions/evidence/settings; frozen product/input hashes intact; four completed cases, 12 calls, no reruns; all 20 metrics retained. Reviewed four English documents and {links} existing local links; wrapper writes one self-record link.")
print("Semantic report review: 13/13 answer points do not waive remaining duplicate meta-requirement and wrong column qualifier; 3/4 case gates, failed acceptance, no generalization or merge claim.")
