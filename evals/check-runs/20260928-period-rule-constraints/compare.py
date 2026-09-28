"""Retain observed-output rejection and explicitly annotated period replay."""
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT / "tests"))
from test_period_rule_constraints import FROZEN, planner_with, recorded, replay_period

target = ROOT / sys.argv[1]
target.mkdir(exist_ok=False)
row = recorded("factual-condition")
planner, sdk = planner_with(row["planner_record"]["output_text"])
try:
    planner.plan(row["case"]["question"], row["case"]["question"], lambda: 30)
except ValueError as error:
    rejection = dict(error_type=type(error).__name__, error=str(error), provider_mock_calls=sdk.responses.create.call_count)
else:
    raise AssertionError("The observed invented rule must not be accepted.")
rows = []
for annotated in [False, True]:
    controller, sdk, payload, answer = replay_period(annotated=annotated)
    value = dict(annotation="Reviewer changes only the two statuses to missing, adds the period mismatch and removes references." if annotated else "Unchanged erroneous live assessment; no automatic semantic repair.",
        plan=controller.prepared.plan.model_dump(mode="json"), assessment=controller.assessment,
        assessment_request=payload, stop_reason=controller.trace["stop_reason"],
        answer=answer, provider_mock_calls=sdk.responses.create.call_count)
    filename = "annotated-missing.json" if annotated else "recorded-wrong-year.json"
    (target / filename).write_text(json.dumps(value, indent=2)+"\n")
    rows.append(dict(artifact=filename, context_sha256=sha256(controller.assessment["context"].encode()).hexdigest(),
        statuses=[p["status"] for p in controller.assessment["requirements"]],
        stop_reason=value["stop_reason"], answer=answer, provider_mock_calls=value["provider_mock_calls"]))
assert rows[0]["context_sha256"] == rows[1]["context_sha256"]
sources = [FROZEN/name for name in ["cases.json", "protocol.md", "factual-condition.json", "missing-year.json", "frozen-evidence.json"]]
summary = dict(historical_product_commit="5447c29", current_base_commit="9a6e65c", source_hashes={str(p.relative_to(PROJECT)):sha256(p.read_bytes()).hexdigest() for p in sources},
    invented_rule=dict(before="Historical live plan accepted the unrequested rule; final answer was correct.",after=rejection,
        consequence="Current validation rejects the plan rather than deleting the rule or making another provider call. A live model that repeats this output will fail the request."),
    period_replays=rows, reviewer="Codex /root; development annotation, no human or independent second review",
    limitation="No live requests. Prompt semantics remain unverified; wrong-year historical output still passes provenance validation. Annotation is a desired decision, not model improvement.")
(target/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(dict(invented_rule=rejection,period_replays=rows),indent=2))
