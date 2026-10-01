"""Audit frozen inputs, provider accounting and report integrity without live calls."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from record_check import METRICS

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
BASE = ROOT.parent / "20260928-planner-fact-scope-acceptance"
preparation = json.loads((ROOT / "preparation.json").read_text())
assert all(sha256((PROJECT / path).read_bytes()).hexdigest() == digest
           for path, digest in preparation["hashes"].items())
assert not subprocess.check_output(["git", "diff", "HEAD", "--", "knowledgebase"], text=True)
assert preparation["settings"] == json.loads((BASE / "preparation.json").read_text())["settings"]
for name in ["run.py", "cases.json", "frozen-evidence.json", "frozen-original-protocol.md"]:
    assert (ROOT / name).read_bytes() == (BASE / name).read_bytes()
assert (ROOT / "baseline-protocol.md").read_bytes() == (BASE / "protocol.md").read_bytes()
measurement = json.loads((ROOT / "measurement.json").read_text())
review = json.loads((ROOT / "review.json").read_text())["cases"]
assert set(measurement["metric_inventory"]) == set(METRICS)
assert measurement["case_gate_pass_count"] == sum(c["case_gate_pass"] for c in review)
assert (measurement["acceptance"] == "passed scoped gates") == all(c["case_gate_pass"] for c in review)
assert measurement["metric_inventory"]["Answer correctness"]["value"]["score"] == sum(p["score"] for c in review for p in c["expected_point_review"] if p["score"] is not None)
events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
starts = [e for e in events if e["kind"] == "start"]
ends = [e for e in events if e["kind"] in {"complete", "error"}]
assert len(starts) == len(ends) <= 12
for case in json.loads((ROOT / "cases.json").read_text()):
    row = json.loads((ROOT / (case["id"] + ".json")).read_text())
    calls = [e for e in starts if e["case"] == case["id"]]
    names = [e["input"].get("text", {}).get("format", {}).get("name", "generation") for e in calls]
    assert names == ["retrieval_plan", "evidence_assessment", "generation"][:len(names)]
    if row["status"] == "completed":
        assert row["planner_record"]["prompt_version"] == "dependent-planner-v7"
        assert row["assessment"]["record"]["prompt_version"] == "evidence-sufficiency-v5"
        assert all(rule in case["question"] for rule in row["plan"]["answer_rules"])
links = 0
for path in [ROOT / "README.md", ROOT / "protocol.md", PROJECT / "docs/v2/README.md", PROJECT / "docs/evidence-sufficiency.md", PROJECT / "docs/planned-retrieval.md"]:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert content.count("\n```") % 2 == 0
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == ROOT / "artifact-review-1.json":
            continue  # The recording wrapper writes the self-record on completion.
        assert target.exists(), (path, link)
        links += 1
    assert all(line == line.rstrip() for line in content.splitlines()), path
for path in ROOT.glob("*.py"):
    ast.parse(path.read_text())
    assert all(line == line.rstrip() for line in path.read_text().splitlines()), path
subprocess.run(["git", "diff", "--check", "--", "docs"], check=True)
print(f"Integrity passed: runner/questions/evidence/settings match baseline; product/input hashes unchanged; {len(starts)} calls accounted for without retries; all 20 metrics retained. Reviewed five English documents and {links} existing local links; wrapper writes one self-record link.")
print("Semantic review and gates remain distinct from provenance checks; report discloses one-attempt development scope, reviewer limits and no end-to-end or merge claim.")
