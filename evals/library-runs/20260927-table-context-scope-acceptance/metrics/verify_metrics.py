"""Validate complete metrics, frozen comparisons and retained live evidence."""

from hashlib import sha256
import json
import sys

from analyze import DIRECTORY, ROOT, read, records, write

sys.path.insert(0, str(ROOT))
from record_check import METRICS


def main():
    measurement = read(DIRECTORY / "measurement.json")
    reviewed = read(ROOT / "review/reviewed-cases.json")["rows"]
    frozen = read(ROOT / "frozen-cases.json")
    baseline = ROOT.parent / "20260927-dense-table-acceptance"
    assert (ROOT / "frozen-cases.json").read_bytes() == (baseline / "frozen-cases.json").read_bytes()
    assert read(ROOT / "index-snapshot.json")["files"] == read(baseline / "index-snapshot.json")["files"]
    binding = read(DIRECTORY / "fact-labels.json")
    baseline_binding = read(ROOT / "frozen-fact-labels.json")
    assert binding["labels"] == baseline_binding["labels"]
    assert binding["children"] == baseline_binding["children"]
    inventories = {**measurement["groups"], "shared_preparation": measurement["shared_preparation"]}
    for group, inventory in inventories.items():
        assert set(inventory) == set(METRICS), group
        for name, value in inventory.items():
            assert value["status"] in {"measured", "not_applicable", "unavailable"}, (group, name)
            assert all(field in value for field in ["value", "unit", "sample_count", "population", "method", "aggregation", "artifact"])
            if value["status"] == "measured":
                assert value["value"] is not None and value["unit"] and value["sample_count"] is not None, (group, name)
            else:
                assert value["value"] is None and value["reason"], (group, name)
    points = [point for row in reviewed for point in row["points"]]
    claims = [claim for row in reviewed for claim in row["factual_claim_groups"]]
    correct = sum(point["reference_correctness"] == point["completeness"] == 1 for point in points)
    supported = sum(claim["context_support"] == claim["citation_support"] == claim["citation_coverage"] == 1 for claim in claims)
    gates = measurement["scoped_gates"]
    assert (gates["requested_points_correct_and_complete"]["numerator"], gates["requested_points_correct_and_complete"]["denominator"]) == (correct, len(points))
    assert (gates["factual_claim_groups_supported_and_individually_cited"]["numerator"], gates["factual_claim_groups_supported_and_individually_cited"]["denominator"]) == (supported, len(claims))
    assert not gates["requested_points_correct_and_complete"]["passed"]
    audit = read(DIRECTORY / "actual-context-audit.json")
    assert len(audit["rows"]) == 6 and audit["provider_calls_during_audit"] == 0
    for row in audit["rows"]:
        assert row["actual_context_equals_packed_evidence"]
        assert sha256((DIRECTORY / row["actual_context_artifact"]).read_bytes()).hexdigest() == row["actual_context_sha256"]
        assert row["actual_context_tokens"] <= row["maximum_context_tokens"] == 4096
    comparisons = measurement["historical_matched_case"]["rows"]
    expected = {(case["id"], arm) for case in frozen["cases"] for arm in ["single", "planned"]}
    assert {(row["case_id"], row["arm"]) for row in comparisons} == expected
    improvements, regressions, unchanged = [], [], []
    for row in comparisons:
        for point in row["points"]:
            outcome = dict(case_id=row["case_id"], arm=row["arm"], fact_id=point["fact_id"],
                           before=point["reference_correctness"]["before"], after=point["reference_correctness"]["after"])
            (improvements if outcome["after"] > outcome["before"] else
             regressions if outcome["after"] < outcome["before"] else unchanged).append(outcome)
    observations = records()
    actual_starts = [row for row in observations if row["kind"] == "sdk_start"]
    usage = measurement["groups"]["all"]["Token usage and cost"]["value"]
    assert usage["sdk_calls_started"] == len(actual_starts) == 27
    assert sum(model["calls"] for model in usage["by_model"].values()) == len(actual_starts)
    assert not usage["terminal_results_without_usage"]
    assert usage["billed_cost"]["status"] == "unavailable" and usage["billed_cost"]["value"] is None
    assert all(row["request"] in {case + "-" + arm for case, arm in expected} for row in actual_starts)
    assert measurement["shared_preparation"]["Token usage and cost"]["status"] == "not_applicable"
    assert measurement["shared_preparation"]["Ingestion and index"]["value"]["upload_parse_index_duration"]["status"] == "not_applicable"
    result = dict(inventories=len(inventories), metrics_per_inventory=len(METRICS), complete_metric_inventory=True,
        requested_points=dict(correct=correct, total=len(points)), supported_claim_groups=dict(supported=supported, total=len(claims)),
        acceptance_remains_failed=True, compared_question_mode_pairs=len(comparisons),
        point_changes=dict(improved=improvements, regressed=regressions, unchanged=unchanged),
        actual_generation_contexts_verified=len(audit["rows"]), same_frozen_corpus_questions_labels=True,
        sdk_calls=len(actual_starts), provider_usage_complete=True, billed_cost_available=False,
        no_new_ingestion=True, provider_calls_during_verification=0)
    write("artifact-review.json", result)
    print(json.dumps(dict(inventories=len(inventories), metrics_per_inventory=len(METRICS),
                         correct_points=f"{correct}/{len(points)}", supported_claims=f"{supported}/{len(claims)}",
                         improved_points=len(improvements), regressed_points=len(regressions),
                         unchanged_points=len(unchanged), sdk_calls=len(actual_starts)), indent=2))


if __name__ == "__main__":
    main()
