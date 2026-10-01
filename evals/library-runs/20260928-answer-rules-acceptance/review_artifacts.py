"""Check retained run integrity and documentation without provider calls."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from record_check import METRICS

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
preparation = json.loads((ROOT / "preparation.json").read_text())
assert all(sha256((PROJECT / path).read_bytes()).hexdigest() == digest
           for path, digest in preparation["hashes"].items())
assert not subprocess.check_output(["git", "diff", "HEAD", "--", "knowledgebase"], text=True)
measurement = json.loads((ROOT / "measurement.json").read_text())
assert set(measurement["metric_inventory"]) == set(METRICS)
assert measurement["acceptance"] == "failed"
assert measurement["case_gate_pass_count"] == 2
assert measurement["metric_inventory"]["Answer correctness"]["value"]["score"] == 11
events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
assert len([e for e in events if e["kind"] == "start"]) == 12
assert len([e for e in events if e["kind"] == "complete"]) == 12
assert not [e for e in events if e["kind"] == "error"]
for identity in ["original-rule", "paraphrased-rule", "factual-condition", "missing-year"]:
    starts = [e for e in events if e["case"] == identity and e["kind"] == "start"]
    assert len(starts) == 3
    row = json.loads((ROOT / (identity + ".json")).read_text())
    assert row["status"] == "completed"
    assert row["planner_record"]["prompt_version"] == "dependent-planner-v4"
    assert row["assessment"]["record"]["prompt_version"] == "evidence-sufficiency-v4"
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
            continue  # Written by the recording wrapper on successful completion.
        assert target.exists(), (path, link)
        links += 1
    assert all(line == line.rstrip() for line in content.splitlines()), path
for path in ROOT.glob("*.py"):
    ast.parse(path.read_text())
    assert all(line == line.rstrip() for line in path.read_text().splitlines()), path
subprocess.run(["git", "diff", "--check", "--", "docs"], check=True)
print(f"Integrity passed: frozen inputs/product unchanged; four completed cases, 12 observed calls, zero reruns; all 20 metrics retained. Reviewed four English documents and {links} existing local links; wrapper writes one self-record link.")
print("Semantic report review: invented rule, altered column qualifier and wrong-year support/answers remain visible; no acceptance, general quality or merge claim.")
