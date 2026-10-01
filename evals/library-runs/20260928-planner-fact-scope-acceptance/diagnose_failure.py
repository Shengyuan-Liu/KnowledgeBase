"""Reproduce the observed planner validation failure without a provider call."""
import json
from pathlib import Path

from pydantic import ValidationError
from knowledgebase.rag.planning import PlanDecision

ROOT = Path(__file__).resolve().parent
events = [json.loads(line) for line in (ROOT / "provider-events.jsonl").read_text().splitlines()]
event = next(e for e in events if e["case"] == "factual-condition" and e["kind"] == "complete")
output = "".join(c["text"] for item in event["result"]["output"] for c in item.get("content", []) if c["type"] == "output_text")
try:
    PlanDecision.model_validate_json(output)
except ValidationError as error:
    errors = error.errors(include_input=False, include_url=False, include_context=False)
    assert len(errors) == 2
    assert all("exactly one {target}" in item["msg"] for item in errors)
else:
    raise AssertionError("The observed invalid dependencies must still fail.")
raw = json.loads(output)
record = dict(case_id="factual-condition", provider_status=event["result"]["status"],
    provider_response_id=event["result"]["id"], original_output=output,
    original_decision=raw, validation_errors=errors,
    diagnosis="The model chose dependent for a logical condition whose entity, document and requested values were already known. Q2/Q3 have no {target}; the existing dependency contract requires exactly one source-derived target placeholder.",
    other_observation="The generated file references contain literal backslash-quote characters in the decoded strings; execution stopped before scope handling, so no downstream filename result was measured.",
    no_repair_or_rerun=True, paid_calls=0)
with (ROOT / "failure-replay.json").open("x") as file:
    file.write(json.dumps(record, indent=2) + "\n")
print(json.dumps(errors, indent=2))
