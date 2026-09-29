"""Review the current docs and retain all checks, including the failed first test."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
comparison = json.loads((HERE / "comparison-1.json").read_text())
assert comparison["paid_calls"] == 0 and len(comparison["rows"]) == 4
for path, digest in comparison["source_hashes"].items():
    assert sha256((PROJECT / path).read_bytes()).hexdigest() == digest
for row in comparison["rows"]:
    assert row["original_and_annotated_requests_identical"]
    assert row["local_input_tokens"]["after"] - row["local_input_tokens"]["before"] == 251
    if row["case_id"] == "factual-condition":
        assert row["original_plan"]["answer_rules"] and row["annotated_plan"]["answer_rules"] == []
    else:
        assert row["original_plan"] == row["annotated_plan"]
for name in ["preparation-1", "focused-1", "focused-2", "comparison-1-check", "scoped-1"]:
    record = json.loads((HERE / (name + ".json")).read_text())
    assert record["exit_code"] == (1 if name == "focused-1" else 0)
    assert len(record["metric_inventory"]) == 20
    assert all(metric["status"] == "not_applicable" and metric["reason"] for metric in record["metric_inventory"].values())
assert json.loads((HERE / "focused-1.json").read_text())["counts"]["failed"] == 1
assert json.loads((HERE / "scoped-1.json").read_text())["counts"]["passed"] == 228

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
            continue  # Created by the wrapper after this review.
        assert target.exists(), (path, link)
        links += 1
subprocess.run(["git", "diff", "--check", "--", "knowledgebase", "tests", "docs"], check=True)
for path in [*HERE.glob("*.py"), PROJECT / "tests/test_factual_condition_rules.py"]:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert all(line == line.rstrip() for line in content.splitlines())
print(f"Reviewed five English documents and {links} local links; wrapper writes one self-record link. All frozen hashes agree and all five prior command records retain 20 metric entries, including the failed attempt.")
print("Content distinguishes guidance from deterministic validation and annotated replay from live model quality. The original semantic failure remains visible; no paid calls or merge claim.")
