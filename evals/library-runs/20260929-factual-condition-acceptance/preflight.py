"""Verify matched inputs and settings before the single paid pass."""
import json
from pathlib import Path

from knowledgebase.providers.planner import PROMPT_VERSION
from knowledgebase.rag.planning import PlanDecision

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "20260929-planner-dependency-acceptance"
for name in ["run.py", "cases.json", "frozen-evidence.json", "frozen-original-protocol.md"]:
    assert (ROOT / name).read_bytes() == (BASE / name).read_bytes()
current = json.loads((ROOT / "preparation.json").read_text())
before = json.loads((BASE / "preparation.json").read_text())
assert current["settings"] == before["settings"]
assert current["context_sha256"] == before["context_sha256"]
assert current["code_commit"].startswith("5541597")
assert PROMPT_VERSION == "dependent-planner-v8"
assert "Exclude factual questions and their conditions" in PlanDecision.model_json_schema()["properties"]["answer_rules"]["description"]
assert PlanDecision.model_json_schema()["$defs"]["DependentQuery"]["properties"]["query_template"]["pattern"] == r"\{target\}"
print("Runner, four questions, frozen evidence and runtime settings match the immediate baseline. Planner v8 and target-presence schema are active; no provider calls yet.")
