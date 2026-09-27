"""Check reviewed artifact identity/provenance and reconcile independent scores."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
RUN = OUT.parent
checks = 0


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


primary = read(OUT / "reviewed-cases.json")
secondary = read(RUN / "root-review.json")
secondary_rows = {(row["case_id"], row["arm"]): row for row in secondary["rows"]}
assessment_review = read(OUT / "assessment-reference-review.json")
frozen = read(RUN / "frozen-cases.json")
cases = {case["id"]: case for case in frozen["cases"]}
observations = (RUN / "server-observations.jsonl").read_text().splitlines()
snapshot = read(RUN / "index-snapshot.json")["files"][0]
canonical = snapshot["extraction"]["text"]
check(primary["manual_judgments_sha256"] == digest(OUT / "manual-judgments.json"), "Manual judgments changed")
check(primary["facts_sha256"] == digest(RUN / "frozen-cases.json"), "Frozen facts changed")
check(primary["sdk_artifact_sha256"] == digest(RUN / "server-observations.jsonl"), "SDK artifact changed")
check(primary["source_hash"] == snapshot["extraction"]["source_hash"], "Wrong original source")
check(primary["extraction_revision_id"] == snapshot["extraction"]["revision_id"], "Wrong extraction revision")
check(primary["original_page_sha256"] == digest(OUT / primary["original_page_artifact"]), "Original page image changed")
check(len(primary["rows"]) == len(secondary_rows) == 6, "Missing review rows")
differences = []

for row in primary["rows"]:
    name = f"{row['case_id']}-{row['arm']}"
    raw_path = RUN / f"{name}.json"
    raw = read(raw_path)
    answer = raw["answer"]
    root = secondary_rows[row["case_id"], row["arm"]]
    check(row["source_artifact_sha256"] == root["raw_sha256"] == digest(raw_path), "Raw response changed")
    check(row["actual_answer"] == root["answer_text"] == answer["answer"], "Actual answer changed")
    check(row["answer_status"] == raw["status"] == "completed", "Request was not completed")
    check([point["fact_id"] for point in row["points"]] == cases[row["case_id"]]["expected_fact_ids"], "Wrong point IDs")
    for point, root_point in zip(row["points"], root["points"], strict=True):
        check(point["reference_fact"] == frozen["facts"][point["fact_id"]], "Review changed a frozen fact")
        for field in ("fact_id", "reference_correctness", "completeness", "supplied_evidence_coverage"):
            if point[field] != root_point[field]:
                differences.append({"request": name, "fact_id": point["fact_id"], "field": field,
                    "primary": point[field], "secondary": root_point[field]})
    check(len(row["factual_claim_groups"]) == len(root["claim_groups"]), "Claim grouping disagreement")
    for claim, root_claim in zip(row["factual_claim_groups"], root["claim_groups"], strict=True):
        check(claim["text"] in answer["answer"], "Claim text changed")
        check(claim["cited_source_ids"] == [int(number) for number in re.findall(r"\[(\d+)\]", claim["text"])], "Citation ID mismatch")
        for field, root_field in (("text", "text"), ("context_support", "faithfulness"),
                                  ("citation_support", "citation_support"), ("citation_coverage", "citation_coverage")):
            if claim[field] != root_claim[root_field]:
                differences.append({"request": name, "claim": claim["text"], "field": field,
                    "primary": claim[field], "secondary": root_claim[root_field]})
    for field, root_field in (("relevance", "answer_relevance"), ("incorrect_abstention", "incorrect_full_abstention")):
        if row[field] != root[root_field]:
            differences.append({"request": name, "field": field, "primary": row[field], "secondary": root[root_field]})
    for sdk in row["generation_sdk_inputs"]:
        actual = json.loads(observations[sdk["line"] - 1])
        saved = read(OUT / sdk["artifact"])
        check(actual == {key: value for key, value in saved.items() if key != "sdk_line"}, "Generation SDK input copy changed")
        check(sdk["call_id"] == actual["call_id"], "Generation call mismatch")
    check(row["history_contract_review"]["raw_history_sources_match"] == raw["history_sources_match"], "Raw parity was repaired")
    check(raw["saved_message"]["content"] == answer["answer"], "Saved answer changed")
    check(raw["saved_message"]["retrieval"] == answer["retrieval"], "Saved retrieval changed")
    for source, saved in zip(answer["sources"], raw["saved_message"]["sources"], strict=True):
        check(source["text"] == canonical[source["start_offset"]:source["end_offset"]], "Source text differs from canonical span")
        check(source == {key: saved[key] for key in source}, "History changed common source fields")
        check({key: value for key, value in saved.items() if key not in source} == {"file_deleted": False}, "Unexpected history-only field")

check(len(assessment_review["rows"]) == 3, "Expected three actual assessments")
for reviewed in assessment_review["rows"]:
    raw = read(RUN / f"{reviewed['case_id']}-planned.json")
    stored = raw["answer"]["retrieval"]["planning"]["hops"]["assessments"][0]
    check(reviewed["raw_model_decision"] == json.loads(stored["record"]["output_text"]), "Raw assessment decision changed")
    for entry, original in zip(reviewed["requirements"], stored["requirements"], strict=True):
        check(entry["normalized_references"] == original["references"], "Selected references changed")
        check(entry["application_added_table_context"] == original["table_context"], "Attached context changed")
        for reference in [*entry["normalized_references"], *entry["application_added_table_context"]]:
            check(reference["quote"] == canonical[reference["start_offset"]:reference["end_offset"]], "Reference source span changed")
            check(reference["page_indices"] == [0], "Wrong reference physical page")

check(sum(len(row["points"]) for row in primary["rows"]) == 24, "Wrong point count")
check(sum(point["reference_correctness"] for row in primary["rows"] for point in row["points"]) == 19, "Wrong point aggregation")
check(sum(len(row["factual_claim_groups"]) for row in primary["rows"]) == 23, "Wrong factual-group count")
check(sum(claim["context_support"] for row in primary["rows"] for claim in row["factual_claim_groups"]) == 19, "Wrong support aggregation")
check(not differences, "Unexpected score disagreement; retain and explain before publishing reconciliation")
with (OUT / "reconciliation.json").open("x") as handle:
    json.dump({"reconciled_at": datetime.now(timezone.utc).isoformat(),
        "primary_artifact": "reviewed-cases.json", "primary_sha256": digest(OUT / "reviewed-cases.json"),
        "primary_manual_judgments_artifact": "manual-judgments.json", "primary_manual_judgments_sha256": digest(OUT / "manual-judgments.json"),
        "secondary_artifact": "../root-review.json", "secondary_sha256": digest(RUN / "root-review.json"),
        "independence": "Primary manual-judgments.json was saved before the root shared its first-pass aggregate; root had saved root-review.json before receiving primary scores. Both then agreed at every requested point and factual group.",
        "disagreements": differences,
        "result": {"correct_complete_points": 19, "requested_points": 24, "supplied_evidence_points": 24,
            "supported_factual_groups": 19, "factual_groups": 23, "incorrect_full_abstentions": 0},
        "assessment_distinction": "All twelve supported statuses are justified as evidence availability. Exact selected rows plus attached headers and cell metadata do not validate the later generated column mapping or the replacement of blanks with zeros.",
        "limits": "Two Codex model reviewers, not humans; agreement is a documented assessment, not ground truth or broad PDF acceptance. No score or raw response was repaired."}, handle, indent=2)
    handle.write("\n")
print(f"{checks} passed, 0 failed, 0 skipped")
print("Artifact identity, provenance and reviewer agreement only; semantic scores remain model-reviewed judgments.")
