"""Compare frozen raw and annotated plans using current production components."""
from hashlib import sha256
import json
from pathlib import Path

from knowledgebase.providers.limits import input_tokens
from test_factual_condition_rules import BASE, recorded, replay_case

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
fixture = json.loads((HERE / "frozen-cases.json").read_text())
hashes = fixture["source_hashes"]
for path, digest in hashes.items():
    assert sha256((PROJECT / path).read_bytes()).hexdigest() == digest
event_path = BASE / "provider-events.jsonl"
hashes[str(event_path.relative_to(PROJECT))] = sha256(event_path.read_bytes()).hexdigest()
events = [json.loads(line) for line in event_path.read_text().splitlines()]
rows = []
for item in fixture["rows"]:
    identity = item["case_id"]
    saved, expected = recorded(identity)
    before, old_controller, old_sdk, old_answer = replay_case(identity, annotated=False)
    after, controller, sdk, answer = replay_case(identity, annotated=True)
    before_calls = [c.kwargs for c in old_sdk.responses.create.call_args_list]
    after_calls = [c.kwargs for c in sdk.responses.create.call_args_list]
    assert before_calls == after_calls
    assert before.plan.model_dump(exclude={"answer_rules"}) == after.plan.model_dump(exclude={"answer_rules"})
    assert after.plan.answer_rules == expected["answer_rules"]
    assert answer == old_answer == saved["answer"]
    assert controller.assessment["context"] == old_controller.assessment["context"] == saved["assessment"]["context"]
    assert controller.assessment["requirements"] == old_controller.assessment["requirements"]
    old_request = next(e["input"] for e in events if e["case"] == identity and e["kind"] == "start")
    new_request = after_calls[0]
    assert new_request["input"][1] == old_request["input"][1]
    schema_before = old_request["text"]["format"]["schema"]
    schema_after = new_request["text"]["format"]["schema"]
    assert "description" not in schema_before["properties"]["answer_rules"]
    assert "Exclude factual questions" in schema_after["properties"]["answer_rules"]["description"]
    old_tokens = input_tokens({"messages": old_request["input"], "schema": schema_before}, "cl100k_base")
    new_tokens = after.record["input_token_count"]
    assert new_tokens <= after.record["max_input_tokens"]
    rows.append(dict(case_id=identity, source_artifact=item["source_artifact"],
        original_plan=before.plan.model_dump(mode="json"), annotated_plan=after.plan.model_dump(mode="json"),
        original_output=before.record["output_text"], annotated_output=after.record["output_text"],
        archived_planner_request=old_request, common_current_requests=after_calls,
        original_and_annotated_requests_identical=True,
        assessment_requirements=controller.assessment["requirements"], frozen_answer=answer,
        context_sha256=sha256(controller.assessment["context"].encode()).hexdigest(),
        stop_reason=controller.trace["stop_reason"], mock_calls_per_arm=len(after_calls),
        local_input_tokens=dict(before=old_tokens, after=new_tokens),
        timeout_note="Mocked local execution; current request model is offline, not the archived provider model. Timings and fabricated mock usage are not production measurements."))
result = dict(scope="Current-code controlled raw/annotated replay plus archived v7/current v8 planner-request comparison; no new inference.",
    reviewer="Codex /root, direct field/request comparison; no independent human review.",
    source_hashes=hashes, rows=rows, paid_calls=0,
    limits="The original bad rule remains accepted. Removing it is a supplied development annotation, not runtime repair or proven model behavior. Original questions, factual plans and all downstream request contents stay identical between controlled arms.")
with (HERE / "comparison-1.json").open("x") as file:
    file.write(json.dumps(result, indent=2) + "\n")
print("Four frozen questions, two controlled arms each; all downstream requests/context and frozen answers unchanged. Only factual-condition answer_rules differs in the annotation.")
print("Mock calls per arm:", {r["case_id"]: r["mock_calls_per_arm"] for r in rows})
print("Local planner input tokens:", {r["case_id"]: r["local_input_tokens"] for r in rows})
print("Original semantic misclassification still accepted; live compliance remains unverified. Paid calls: 0.")
