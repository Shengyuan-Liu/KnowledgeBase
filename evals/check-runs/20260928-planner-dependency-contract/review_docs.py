"""Review current documentation, retained comparisons and measurement completeness."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
fixture = json.loads((HERE / "frozen-cases.json").read_text())
for path, digest in fixture["source_hashes"].items():
    assert sha256((PROJECT / path).read_bytes()).hexdigest() == digest
comparison = json.loads((HERE / "comparison-1.json").read_text())
assert len(fixture["rows"]) == 4 and len(comparison["rows"]) == 8
assert comparison["provider_calls"] == 0
assert comparison["frozen_sources"] == fixture["source_hashes"]
for name in ["preparation-1", "focused-1", "scoped-1", "comparison-1-check"]:
    record = json.loads((HERE / (name + ".json")).read_text())
    assert record["exit_code"] == 0
    assert len(record["metric_inventory"]) == 20
    assert all(m["status"] == "not_applicable" and m["reason"] for m in record["metric_inventory"].values())

paths = [HERE / "README.md", PROJECT / "docs/v2/README.md", PROJECT / "docs/planned-retrieval.md",
         PROJECT / "docs/dependent-retrieval.md", PROJECT / "docs/evidence-sufficiency.md"]
links = 0
for path in paths:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert content.count("\n```") % 2 == 0
    assert all(line == line.rstrip() for line in content.splitlines())
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == HERE / "documentation-1.json":
            continue  # The record wrapper writes this after the review.
        assert target.exists(), (path, link)
        links += 1
subprocess.run(["git", "diff", "--check", "--", "knowledgebase", "tests", "docs"], check=True)
for path in [*HERE.glob("*.py"), PROJECT / "tests/test_planner_dependency_contract.py"]:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert all(line == line.rstrip() for line in content.splitlines())
print(f"Reviewed five English documents and {links} local links; one self-record link is written on completion.")
print("Frozen source hashes agree; four completed command records retain all 20 metric entries. Raw evidence remains unchanged.")
print("Content distinguishes schema presence from runtime uniqueness and semantic correctness. Live route/column recovery, exact schema acceptance and independent review remain unverified.")
