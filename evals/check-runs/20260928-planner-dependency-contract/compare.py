"""Compare recorded planner requests with current mocked requests, without inference."""
from hashlib import sha256
import json
from pathlib import Path
import re

from pydantic import ValidationError

from knowledgebase.providers.limits import input_tokens
from test_period_rule_constraints import planner_with

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
fixture = json.loads((HERE / "frozen-cases.json").read_text())
for path, digest in fixture["source_hashes"].items():
    assert sha256((PROJECT / path).read_bytes()).hexdigest() == digest

rows = []
for frozen in fixture["rows"]:
    question = frozen["case"]["question"]
    for variant in ["original", "annotated"]:
        output = frozen["original_output"] if variant == "original" else json.dumps(frozen["annotated_decision"])
        planner, sdk = planner_with(output)
        planner.model = frozen["original_request"]["model"]
        try:
            result = planner.plan(question, question, lambda: 30)
            plan, errors = result.plan.model_dump(mode="json"), []
        except ValidationError as error:
            plan = None
            errors = error.errors(include_input=False, include_url=False, include_context=False)
        request = sdk.responses.create.call_args.kwargs
        before = frozen["original_request"]
        assert request["input"][1] == before["input"][1]
        assert request["model"] == before["model"]
        assert request["max_output_tokens"] == before["max_output_tokens"]
        assert sdk.responses.create.call_count == 1
        before_schema = before["text"]["format"]["schema"]
        after_schema = request["text"]["format"]["schema"]
        pattern = after_schema["$defs"]["DependentQuery"]["properties"]["query_template"]["pattern"]
        templates = [d["query_template"] for d in json.loads(output)["dependencies"]]
        rows.append(dict(case_id=frozen["case"]["id"], variant=variant, current_request=request,
            supplied_mock_output=output, returned_plan=plan, validation_errors=errors,
            provider_mock_calls=1, provider_calls=0, max_retries=sdk.with_options.call_args.kwargs["max_retries"],
            old_schema_has_target_pattern="pattern" in before_schema["$defs"]["DependentQuery"]["properties"]["query_template"],
            current_pattern_rejects_templates=[t for t in templates if not re.search(pattern, t)],
            local_serialized_input_tokens=dict(before=input_tokens({"messages": before["input"], "schema": before_schema}, "cl100k_base"),
                                              after=input_tokens({"messages": request["input"], "schema": after_schema}, "cl100k_base"))))

condition = [r for r in rows if r["case_id"] == "factual-condition"]
assert len(condition[0]["validation_errors"]) == 2
assert condition[1]["returned_plan"]["route"] == "decomposed"
assert len(condition[1]["returned_plan"]["queries"]) == 3
assert all(r["local_serialized_input_tokens"]["after"] <= 8192 for r in rows)
result = dict(scope="Offline production planner with controlled provider outputs; old requests are recorded live artifacts, not new baseline calls.",
    reviewer="Codex /root; exact field and request comparison, not human or independent semantic review.",
    limits="The pattern rejects targetless templates, not semantically wrong routes or transferred column modifiers. Annotated outputs test contracts, not model compliance. Reused questions are development regressions, not held-out evaluation.",
    frozen_sources=fixture["source_hashes"], rows=rows, provider_calls=0)
with (HERE / "comparison-1.json").open("x") as file:
    file.write(json.dumps(result, indent=2) + "\n")
print("Compared four frozen questions, original and annotated outputs: 8 one-call mocked planner replays; 0 paid calls.")
print("The two recorded targetless templates now fail the transmitted presence pattern; runtime rejects their unchanged output. Annotated three-query decomposition passes.")
print("The original column qualifier error is still accepted; the annotated correction is preserved. No measured semantic improvement is claimed.")
print("Local serialized planner input tokens before/after:", [(r["case_id"], r["local_serialized_input_tokens"]) for r in rows if r["variant"] == "original"])
