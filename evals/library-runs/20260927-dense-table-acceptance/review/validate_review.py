"""Check review artifact identity and provenance, not semantic judgments."""

import hashlib
import json
from pathlib import Path
import re

DIRECTORY = Path(__file__).resolve().parent
RUN = DIRECTORY.parent
checks = 0


def read(path):
    return json.loads(path.read_text())


def check(condition, message):
    global checks
    assert condition, message
    checks += 1


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


review = read(DIRECTORY / "reviewed-cases.json")
audit = read(DIRECTORY / "assessment-reference-review.json")
reconciliation = read(DIRECTORY / "reconciliation.json")
root = read(RUN / "root-review.json")
root_rows = {(r["case_id"], r["arm"]): r for r in root["rows"]}
frozen = read(RUN / "frozen-cases.json")
cases = {case["id"]: case for case in frozen["cases"]}
snapshot = read(RUN / "index-snapshot.json")["files"][0]
canonical = snapshot["extraction"]["text"]
observations = (RUN / "server-observations.jsonl").read_text().splitlines()
check(review["facts_sha256"] == digest(RUN / "frozen-cases.json"), "Frozen facts changed")
check(review["sdk_artifact_sha256"] == digest(RUN / "server-observations.jsonl"), "SDK observations changed")
check(review["original_page_sha256"] == digest(DIRECTORY / review["original_page_artifact"]), "Original page changed")
check(review["source_hash"] == snapshot["extraction"]["source_hash"], "Wrong original source")
check(review["extraction_revision_id"] == snapshot["extraction"]["revision_id"], "Wrong extraction revision")
check(reconciliation["primary_sha256"] == digest(DIRECTORY / "reviewed-cases.json"), "Primary review changed after reconciliation")
check(reconciliation["secondary_sha256"] == digest(RUN / "root-review.json"), "Root review changed after reconciliation")
check(len(review["rows"]) == 6, "Expected six reviewed requests")

for row in review["rows"]:
    raw_path = DIRECTORY / row["source_artifact"]
    raw = read(raw_path)
    root_row = root_rows[row["case_id"], row["arm"]]
    answer = raw["answer"]
    check(row["source_artifact_sha256"] == digest(raw_path), "Raw response changed")
    check(row["actual_answer"] == answer["answer"], "Review changed the actual answer")
    check(row["answer_status"] == raw["status"] == "completed", "Wrong request status")
    check([p["fact_id"] for p in row["points"]] == cases[row["case_id"]]["expected_fact_ids"], "Wrong expected points")
    for point, root_point in zip(row["points"], root_row["points"]):
        check(all(point[key] == root_point[key] for key in root_point), "Unreported point-score disagreement")
        check(point["reference_fact"] == frozen["facts"][point["fact_id"]], "Fact mutated in review")
    check(len(row["factual_claim_groups"]) == len(root_row["claim_groups"]), "Unreported claim grouping disagreement")
    for claim, root_claim in zip(row["factual_claim_groups"], root_row["claim_groups"]):
        check(claim["text"] in answer["answer"], "Claim text not preserved")
        check(claim["context_support"] == root_claim["faithfulness"], "Unreported faithfulness disagreement")
        check(claim["citation_support"] == root_claim["citation_support"], "Unreported citation-support disagreement")
        check(claim["citation_coverage"] == root_claim["citation_coverage"], "Unreported citation-coverage disagreement")
        check(claim["cited_source_ids"] == [int(n) for n in re.findall(r"\[(\d+)\]", claim["text"])], "Wrong citation IDs")
    check(bool(row["incorrect_abstention"]) == root_row["incorrect_full_abstention"], "Unreported refusal disagreement")
    for source in answer["sources"]:
        check(source["text"] == canonical[source["start_offset"]:source["end_offset"]], "Changed canonical source span")
        check(source["pdf"]["tables"] == [] and source["pdf"]["supplements"] == [], "Unexpected supplied table evidence")
        check(source["file_id"] == snapshot["file"]["file_id"], "Wrong supplied file ID")
    for sdk in row["generation_sdk_inputs"]:
        event = json.loads(observations[sdk["line"] - 1])
        check(event["call_id"] == sdk["call_id"], "Wrong SDK call pointer")
        actual_user = next(m["content"] for m in event["input"]["input"] if m["role"] == "user")
        check(actual_user == sdk["user_message"], "Changed actual SDK user input")
        check(all(source["text"] in actual_user for source in answer["sources"]), "Returned source absent from actual SDK input")
    history = row["history_contract_review"]
    check(history["raw_history_sources_match"] == raw["history_sources_match"], "Raw equality flag repaired")
    check(raw["saved_message"]["content"] == answer["answer"], "Saved answer changed")
    check(raw["saved_message"]["retrieval"] == answer["retrieval"], "Saved retrieval changed")
    check(len(raw["saved_message"]["sources"]) == len(answer["sources"]), "Saved source count changed")
    for original, saved in zip(answer["sources"], raw["saved_message"]["sources"]):
        check(original == {key: saved[key] for key in original}, "Shared source fields changed")
        check({key: value for key, value in saved.items() if key not in original} == {"file_deleted": False}, "Unexpected history-only fields")

for row in audit["rows"]:
    if row["origin"] == "provider_assessment":
        raw = read(RUN / f"{row['case_id']}-planned.json")
        stored = raw["answer"]["retrieval"]["planning"]["hops"]["assessments"][row["round_index"] - 1]
        check(row["raw_model_decision"] == json.loads(stored["record"]["output_text"]), "Raw assessment decision changed")
        for reviewed, normalized, selected in zip(row["requirements"], stored["requirements"], row["raw_model_decision"]["requirements"]):
            check(reviewed["raw_model_selected_references"] == selected["references"], "Raw selected reference changed")
            check(reviewed["normalized_references"] == normalized["references"], "Normalized reference changed")
            check(reviewed["application_added_table_context"] == normalized["table_context"] == [], "Unexpected attached table context")
            for ref in reviewed["normalized_references"]:
                check(ref["quote"] == canonical[ref["start_offset"]:ref["end_offset"]], "Selected exact span changed")
                check(ref["source_number"] == 1 and ref["file_id"] == snapshot["file"]["file_id"], "Selected reference has wrong current source identity")

check(sum(len(r["points"]) for r in review["rows"]) == 24, "Requested-point count mismatch")
check(sum(len(r["factual_claim_groups"]) for r in review["rows"]) == 5, "Factual-group count mismatch")
check(len(reconciliation["disagreements"]) == 3 and all(d["metric"] == "relevance" for d in reconciliation["disagreements"]), "Relevance sensitivity missing")
print(f"{checks} passed, 0 failed, 0 skipped")
print("Artifact identity/provenance only; semantic scores remain model-reviewed judgments, not test-proven truth.")
