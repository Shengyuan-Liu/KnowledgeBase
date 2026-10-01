"""Compare published and provider schemas with the pre-refactor snapshot."""

import json
from pathlib import Path

from knowledgebase import schemas


def contract(value):
    if isinstance(value, dict):
        return {key: sorted(item) if key == "required" else contract(item)
                for key, item in value.items() if key != "description"}
    if isinstance(value, list):
        return [contract(item) for item in value]
    return value


before = json.loads(Path(__file__).with_name("schema-before.json").read_text())
for name, expected in before.items():
    actual = getattr(schemas, name).model_json_schema()
    assert contract(actual) == contract(expected), name
    if name in {"PlanDecision", "TargetDecisions", "SufficiencyAssessment"}:
        assert actual == expected, f"Provider schema changed: {name}"
print(f"{len(before)} schema contracts unchanged; provider schemas byte-structure equivalent.")
print("Only documentation descriptions and ordering of required fields ignored for API/PDF schemas.")
