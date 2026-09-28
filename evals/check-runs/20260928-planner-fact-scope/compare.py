"""Compare frozen bad and annotated intended decisions, without provider calls."""
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT / "tests"))
from test_planner_fact_scope import replay_scope

target = ROOT / sys.argv[1]
target.mkdir(exist_ok=False)
fixture = json.loads((ROOT / "frozen-case.json").read_text())
assert sha256((PROJECT / fixture["source_artifact"]).read_bytes()).hexdigest() == fixture["source_sha256"]
rows = []
for annotated in [False, True]:
    controller, sdk, answer, _ = replay_scope(annotated=annotated)
    arm = "annotated-two-facts" if annotated else "recorded-duplicate-check"
    value = dict(arm=arm, annotated_provider_outputs=annotated,
        plan=controller.prepared.plan.model_dump(mode="json"), planner_record=controller.prepared.record,
        assessment=controller.assessment, stop_reason=controller.trace["stop_reason"], answer=answer,
        provider_mock_calls=sdk.responses.create.call_count,
        requests=[call.kwargs for call in sdk.responses.create.call_args_list])
    (target/(arm+".json")).write_text(json.dumps(value,indent=2)+"\n")
    rows.append(dict(artifact=arm+".json", annotated_provider_outputs=annotated,
        requirement_count=len(controller.prepared.plan.requirements), query_count=len(controller.prepared.plan.queries),
        statuses=[p["status"] for p in controller.assessment["requirements"]],
        answer=answer, provider_mock_calls=value["provider_mock_calls"],
        context_sha256=sha256(controller.assessment["context"].encode()).hexdigest()))
assert rows[0]["context_sha256"] == rows[1]["context_sha256"]
summary = dict(base_commit="6bdcf47", source_artifact=fixture["source_artifact"], source_sha256=fixture["source_sha256"],
    annotation=fixture["annotation"], rows=rows,
    comparison_scope="Both arms use current code with controlled provider responses. Historical bad semantics are preserved. This is not a live before/after model comparison.",
    quality_limit="The annotated plan/assessment are supplied by the reviewer; no semantic quality gain is measured. The local insufficient-evidence answer is less specific than a generated period explanation.")
(target/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(rows,indent=2))
