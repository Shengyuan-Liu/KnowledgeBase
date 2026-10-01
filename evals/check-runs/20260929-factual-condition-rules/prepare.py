"""Freeze the observed condition/rule duplication without changing historical data."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BASE = PROJECT / "evals/library-runs/20260929-planner-dependency-acceptance"
cases = json.loads((BASE / "cases.json").read_text())
rows = []
sources = [BASE / "cases.json", BASE / "frozen-evidence.json", BASE / "review.json"]
for case in cases:
    path = BASE / (case["id"] + ".json")
    sources.append(path)
    saved = json.loads(path.read_text())
    expected = deepcopy(json.loads(saved["planner_record"]["output_text"]))
    if case["id"] == "factual-condition":
        assert expected["answer_rules"] and all(rule in case["question"] for rule in expected["answer_rules"])
        expected["answer_rules"] = []
    rows.append(dict(case_id=case["id"], source_artifact=str(path.relative_to(PROJECT)),
                     expected_decision=expected))
fixture = dict(source_hashes={str(p.relative_to(PROJECT)): sha256(p.read_bytes()).hexdigest() for p in sources},
    annotation_author="Codex /root; development expectation, not a model result or independent human review.",
    annotation_method="Only remove the duplicated factual conditional question from answer_rules in factual-condition. Preserve every other plan field, and all other cases, byte-equivalent as parsed JSON. Questions, supplied evidence and actual downstream outputs remain frozen in linked artifacts.",
    rows=rows)
with (HERE / "frozen-cases.json").open("x") as file:
    file.write(json.dumps(fixture, indent=2) + "\n")
print("Frozen four prior case artifacts and shared evidence by SHA-256; one explicitly annotated answer_rules correction. No provider calls.")
