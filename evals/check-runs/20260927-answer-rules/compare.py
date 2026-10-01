"""Compare controlled classification outputs with identical frozen evidence."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
sys.path.insert(0, str(ROOT / "tests"))
from test_answer_rules import replay_controller
from record_check import METRICS


def read(path):
    return json.loads(path.read_text())


if __name__ == "__main__":
    target = DIRECTORY / sys.argv[1]
    target.mkdir(exist_ok=False)
    fixture = read(DIRECTORY / "frozen-case.json")
    original = ROOT / fixture["source_artifact"]
    assert sha256(original.read_bytes()).hexdigest() == fixture["sha256"]
    baseline = original.parent
    spec = importlib.util.spec_from_file_location("frozen_metrics", baseline / "metrics/analyze.py")
    metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metrics)
    frozen = read(baseline / "frozen-cases.json")
    facts = next(c["expected_fact_ids"] for c in frozen["cases"] if c["id"] == "grouped-and-blank-cells")
    labels = read(baseline / "frozen-fact-labels.json")["labels"]
    documents = {d["file"]["file_id"]: d for d in read(baseline / "index-snapshot.json")["files"]}
    sources = read(original)["answer"]["sources"]
    coverage = metrics.supplied_coverage(sources, facts, labels, documents)
    assert coverage["value"] == 1
    rows, contexts, catalogs = [], [], []
    for separated in [False, True]:
        controller, sdk, _ = replay_controller(separated=separated)
        context = controller.assessment["context"]
        contexts.append(context)
        catalogs.append(controller.assessment["evidence_catalog"])
        arm = "annotated_separation" if separated else "recorded_classification"
        row = dict(arm=arm, stop_reason=controller.trace["stop_reason"],
                   plan=controller.prepared.plan.model_dump(mode="json"),
                   planner_record=controller.prepared.record,
                   assessment=controller.assessment,
                   provider_requests=[call.kwargs for call in sdk.responses.create.call_args_list],
                   supplementary_queries=controller.trace["supplementary_queries"],
                   context_sha256=sha256(context.encode()).hexdigest(),
                   frozen_supplied_evidence_coverage=coverage)
        (target / f"{arm}.json").write_text(json.dumps(row, indent=2) + "\n")
        rows.append(dict(arm=arm, stop_reason=row["stop_reason"], requirements=len(row["plan"]["requirements"]),
                         answer_rules=len(row["plan"]["answer_rules"]), queries=len(row["plan"]["queries"]),
                         context_sha256=row["context_sha256"], coverage=coverage["value"]))
    assert contexts[0] == contexts[1] and catalogs[0] == catalogs[1]
    inventory = {metric: dict(status="not_applicable", value=None, unit=None,
        reason="Controlled provider-output replay; no new retrieval, answer generation, provider calls or production workload.",
        sample_count=None, population="offline replay", method="not exercised", aggregation="none", artifact=None)
        for metric in METRICS}
    inventory["Final evidence coverage"] = dict(status="measured", value=1.0, unit="fraction of frozen facts",
        reason=None, sample_count=4, numerator=4, denominator=4, population="one question, identical evidence in both arms",
        method="Original source-bound cell/header/row checks reused; exact replay context and catalog are identical. This is frozen supplied-evidence coverage, not a new retrieval measurement.",
        aggregation="fully covered facts / four requested facts", artifact="recorded_classification.json and annotated_separation.json")
    summary = dict(comparison_type="controlled provider-output contract; both arms use current code",
        annotation=fixture["classification_annotation"], rows=rows, metric_inventory=inventory,
        live_classification_quality=dict(status="unavailable", reason="Revised prompts have not been called against a live model."))
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(rows, indent=2))
