"""Preserve independent manual judgments with exact source and SDK provenance.

This serializer does not derive semantic scores from text matching. Scores are
the prior manual judgments. Structural checks verify the evidence being reviewed.
No API calls or production edits are performed; output files are exclusive.
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
RUN = OUT.parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def cell_tuple(cell):
    return [cell[key] for key in ("row_start", "row_end", "column_start", "column_end", "start_offset", "end_offset")]


def covered(source, start, end):
    return source["start_offset"] <= start <= end <= source["end_offset"]


judgments = read(OUT / "manual-judgments.json")
frozen = read(RUN / "frozen-cases.json")
cases = {row["id"]: row for row in frozen["cases"]}
labels = read(RUN / "frozen-fact-labels.json")["labels"]
document = read(RUN / "index-snapshot.json")["files"][0]
canonical = document["extraction"]["text"]
observations = [(line, json.loads(text)) for line, text in enumerate((RUN / "server-observations.jsonl").read_text().splitlines(), 1)]
runtime = read(RUN / "resolved-runtime.json")
reviewer = judgments["reviewer"]
rows, assessments = [], []


def matching_sources(fact_id, sources):
    label = labels[fact_id]
    matches = []
    for source in sources:
        if source["file_id"] != label["file_id"] or source["pdf"]["source_hash"] != label["source_hash"]:
            continue
        if fact_id == "checks_not_sales":
            if covered(source, 5449, 5738):
                matches.append(source["source_id"])
            continue
        required = [label["target_cell"], label["row_label_cell"], label["period_cell"], *label["header_cells"]]
        tables = [table for table in source["pdf"]["tables"] if table["table_id"] == label["table_id"]]
        if (all(covered(source, cell["start_offset"], cell["end_offset"]) for cell in required)
                and all(any(cell_tuple(cell) in table["cells"] for table in tables) for cell in required)
                and any(region["page_index"] == 0 for region in source["pdf"]["regions"])):
            matches.append(source["source_id"])
    return matches


for manual in judgments["rows"]:
    case_id, arm = manual["case_id"], manual["arm"]
    name = f"{case_id}-{arm}"
    raw_path = RUN / f"{name}.json"
    raw = read(raw_path)
    answer = raw["answer"]
    sources = answer["sources"]
    case = cases[case_id]
    calls = [(line, event) for line, event in observations if event["kind"] == "sdk_start"
             and event.get("api") == "responses" and event["request"] == name]
    generation = [(line, event) for line, event in calls if event["input"].get("stream")]
    assert len(generation) == 1
    line, event = generation[0]
    actual_user = next(message["content"] for message in event["input"]["input"] if message["role"] == "user")
    context = actual_user.split("\n\nSources:\n", 1)[1]
    sections = re.split(r"(?m)^\[(\d+)\]\nSource metadata: ", context)
    numbered = dict(zip((int(number) for number in sections[1::2]), sections[2::2], strict=True))
    assert len(numbered) == len(sources)
    for source in sources:
        assert source["text"] == canonical[source["start_offset"]:source["end_offset"]]
        block = numbered[source["source_id"]]
        assert f'Excerpt:\n{source["text"]}\nPDF physical pages: 1' in block
        assert f'Excerpt canonical offsets: {source["start_offset"]}:{source["end_offset"]}' in block
        table_lines = [entry for entry in block.splitlines() if entry.startswith("Table cells [")]
        expected_tables = [{key: value for key, value in table.items() if key != "column_header_spans"}
                           for table in source["pdf"]["tables"]]
        assert (json.loads(table_lines[0].split(": ", 1)[1]) if table_lines else []) == expected_tables
    save(f"{name}-actual-generation-input.json", {"sdk_line": line, **event})
    body_lines = answer["answer"].splitlines()
    claims = [text.strip()[2:] for index, text in enumerate(body_lines)
              if text.strip().startswith("- ") and index not in manual["excluded_line_indices"]]
    assert len(claims) == len(manual["claim_scores"]) == len(manual["claim_fact_ids"])
    assert len(manual["point_scores"]) == len(case["expected_fact_ids"])
    points = []
    for fact_id, score in zip(case["expected_fact_ids"], manual["point_scores"], strict=True):
        source_ids = matching_sources(fact_id, sources)
        assert source_ids, f"Expected structural support for {name}/{fact_id}"
        label = labels[fact_id]
        proof = ({"disclaimer_span": [5449, 5738], "page_index": 0} if fact_id == "checks_not_sales" else {
            "target_cell": label["target_cell"], "row_label_cell": label["row_label_cell"],
            "period_cell": label["period_cell"], "header_cells": label["header_cells"],
            "table_id": label["table_id"], "row_span": label["row_span"], "row_text": label["row_text"],
        })
        points.append({"fact_id": fact_id, "reference_correctness": score, "completeness": score,
            "supplied_evidence_coverage": 1, "source_ids_with_matching_anchors": source_ids,
            "reference_fact": frozen["facts"][fact_id], "structural_evidence": proof,
            "evidence_note": manual["note"]})
    claim_groups = []
    for text, score, fact_ids in zip(claims, manual["claim_scores"], manual["claim_fact_ids"], strict=True):
        cited_ids = [int(number) for number in re.findall(r"\[(\d+)\]", text)]
        if score:
            assert all(set(cited_ids).intersection(matching_sources(fact_id, sources)) for fact_id in fact_ids)
        claim_groups.append({"text": text, "fact_ids": fact_ids, "original_page_correctness": score,
            "context_support": score, "cited_source_ids": cited_ids, "citation_support": score,
            "citation_coverage": score, "supporting_evidence_artifact": f"../{name}.json#answer.sources",
            "note": manual["note"]})
    saved_sources = raw["saved_message"]["sources"]
    shared_match = len(sources) == len(saved_sources) and all(
        source == {key: saved[key] for key in source} for source, saved in zip(sources, saved_sources))
    extras = [{key: value for key, value in saved.items() if key not in source}
              for source, saved in zip(sources, saved_sources)]
    assert shared_match and all(extra == {"file_deleted": False} for extra in extras)
    assert raw["saved_message"]["content"] == answer["answer"]
    assert raw["saved_message"]["retrieval"] == answer["retrieval"]
    rows.append({"pass_name": "table_context_scope_acceptance", "case_id": case_id, "arm": arm,
        "answer_status": raw["status"], "actual_answer": answer["answer"],
        "source_artifact": f"../{name}.json", "source_artifact_sha256": digest(raw_path),
        "generation_sdk_inputs": [{"artifact": f"{name}-actual-generation-input.json",
            "source_artifact": "../server-observations.jsonl", "line": line, "call_id": event["call_id"]}],
        "source_provenance": [{key: source[key] for key in ("source_id", "file_id", "file_name", "chunk_id", "start_offset", "end_offset", "pdf")} for source in sources],
        "points": points, "factual_claim_groups": claim_groups,
        "excluded_framing": [{"text": body_lines[index], "reason": "Introductory restatement; the following distinct numeric bullets are scored individually."} for index in manual["excluded_line_indices"]],
        "missing_point_review": [], "relevance": 1, "full_abstention": False,
        "appropriate_abstention": None, "appropriate_abstention_status": judgments["shared_judgments"]["appropriate_abstention_reason"],
        "incorrect_abstention": 0, "note": manual["note"],
        "history_contract_review": {"raw_history_matches": raw["history_matches"],
            "raw_history_sources_match": raw["history_sources_match"],
            "raw_history_retrieval_matches": raw["history_retrieval_matches"],
            "common_source_fields_match": shared_match, "history_only_source_fields": extras,
            "note": "Raw source equality remains false because history adds file_deleted=false. All shared evidence fields, answer text and retrieval metadata are unchanged."}})
    if arm == "planned":
        assessment_calls = [(line, event) for line, event in calls
            if event["input"].get("text", {}).get("format", {}).get("name") == "evidence_assessment"]
        stored = answer["retrieval"]["planning"]["hops"]["assessments"]
        assert len(stored) == len(assessment_calls) == 1
        assessment = stored[0]
        sdk_line, sdk = assessment_calls[0]
        assert assessment["record"]["input"] == sdk["input"]["input"]
        payload = json.loads(next(message["content"] for message in sdk["input"]["input"] if message["role"] == "user"))
        raw_decision = json.loads(assessment["record"]["output_text"])
        decisions = {requirement["requirement_id"]: requirement for requirement in raw_decision["requirements"]}
        reviewed_requirements = []
        for requirement, fact_id in zip(assessment["requirements"], case["expected_fact_ids"], strict=True):
            raw_refs = decisions[requirement["requirement_id"]]["references"]
            refs, attached = requirement["references"], requirement["table_context"]
            assert [reference["evidence_id"] for reference in raw_refs] == [reference["evidence_id"] for reference in refs]
            for reference in [*refs, *attached]:
                assert reference["quote"] == canonical[reference["start_offset"]:reference["end_offset"]]
                assert f'[{reference["evidence_id"]}] {reference["quote"]}' in payload["context"]
                assert reference["page_indices"] == [0]
            reviewed_requirements.append({"fact_id": fact_id, "requirement_id": requirement["requirement_id"],
                "description": requirement["description"], "status": requirement["status"], "gap": requirement["gap"],
                "raw_model_selected_references": raw_refs, "normalized_references": refs,
                "application_added_table_context": attached, "selected_ids_preserved": True,
                "exact_reference_spans_preserved": True,
                "selected_references_alone_include_complete_headers_and_period": fact_id == "checks_not_sales",
                "complete_with_application_context_and_supplied_table_coordinates": True,
                "status_supported_by_actual_assessment_context": True,
                "note": ("The selected disclaimer paragraph directly contains both required clauses." if fact_id == "checks_not_sales" else
                    "The selected state row contains the required value or explicit blank. Attached title/month/group/leaf-header passages and supplied cell-coordinate tuples complete its source meaning. Model-selected IDs are preserved; added context is separately labeled. Supported is an evidence-availability judgment, not a verified interpretation of the downstream generated number.")})
        assessments.append({"case_id": case_id, "arm": arm, "round_index": assessment["round_index"],
            "origin": "provider_assessment", "sdk_input": {"artifact": "../server-observations.jsonl", "line": sdk_line, "call_id": sdk["call_id"]},
            "raw_model_decision": raw_decision, "requirements": reviewed_requirements,
            "supplementary_query_review": "All requirements were marked supported after the first assessment; no supplementary queries were proposed.",
            "table_context_effectiveness": "Full required table context is available and linked. The grouped answer still misinterprets columns/blanks, so availability and exact reference provenance do not establish correct answer semantics."})

baseline_path = RUN.parent / "20260927-dense-table-acceptance/review/reviewed-cases.json"
baseline_rows = {(row["case_id"], row["arm"]): row for row in read(baseline_path)["rows"]}
comparison = []
for row in rows:
    before = baseline_rows[row["case_id"], row["arm"]]
    comparison.append({"case_id": row["case_id"], "arm": row["arm"],
        "before_correct_points": sum(point["reference_correctness"] for point in before["points"]),
        "after_correct_points": sum(point["reference_correctness"] for point in row["points"]),
        "requested_points": len(row["points"]),
        "before_supported_groups": sum(claim["context_support"] for claim in before["factual_claim_groups"]),
        "before_claim_groups": len(before["factual_claim_groups"]),
        "after_supported_groups": sum(claim["context_support"] for claim in row["factual_claim_groups"]),
        "after_claim_groups": len(row["factual_claim_groups"]),
        "before_full_abstention": before["full_abstention"], "after_full_abstention": row["full_abstention"],
        "note": row["note"]})

review = {"reviewer": reviewer, "reviewed_at": datetime.now(timezone.utc).isoformat(),
    "code_version": runtime["code_commit"], "independence": judgments["independence"],
    "manual_judgments_sha256": digest(OUT / "manual-judgments.json"),
    "rubric": "../frozen-original-protocol.md and review-plan.md; unchanged requested-point and factual paragraph/bullet rubric.",
    "facts_artifact": "../frozen-cases.json", "facts_sha256": digest(RUN / "frozen-cases.json"),
    "source_hash": frozen["corpus"][0]["sha256"], "extraction_revision_id": document["extraction"]["revision_id"],
    "original_page_artifact": "../../20260927-v2-pdf-live/source-review/background-checks-1.png",
    "original_page_sha256": frozen["source_annotations"]["original_page_sha256"],
    "original_page_review": "Uses unchanged original-page gold and previously reviewed image; no new browser viewer click is claimed.",
    "sdk_artifact": "../server-observations.jsonl", "sdk_artifact_sha256": digest(RUN / "server-observations.jsonl"),
    "grouping_decisions": ["The dense single outer bullet and state single introduction restate the requested comparison; they are excluded with exact text. Each numeric nested bullet is its own group.",
        "The grouped single Rentals bullet contains two wrong cell claims; it remains one entirely unsupported group. Planned Rentals claims occur in two bullets and count separately.",
        "All six responses attempt substantive answers, have no missing-information or operational-refusal statements, and are fully relevant independently of accuracy."],
    "blank_cell_review": {"status": "measured", "single": "Both blanks were replaced with Redemption values 2,179 and 2,307.",
        "planned": "Both blanks were incorrectly reported as zero; Pre-Pawn Handgun also received Redemption Handgun 2,179 instead of 14.",
        "evidence_available": "Both actual generation inputs contain the full Alabama row, empty cells 434:434 and 435:435 at columns 16 and 17, Rentals parent 16:18 and corresponding leaf headers, month and page 1.",
        "observable_evidence_required": frozen["blank_evidence_rule"]},
    "baseline_comparison": {"artifact": "../../20260927-dense-table-acceptance/review/reviewed-cases.json",
        "artifact_sha256": digest(baseline_path), "historical_scores_preserved": True, "rows": comparison,
        "comparability_limits": "Same three questions, original PDF, frozen facts, retained extraction/index and settings; product scope/context/packing repairs differ. Provider outputs and timings remain stochastic, and only one request per question/mode exists in each run. No held-out generalization claim."},
    "rows": rows}
save("reviewed-cases.json", review)
save("assessment-reference-review.json", {"reviewer": reviewer, "reviewed_at": review["reviewed_at"],
    "code_version": review["code_version"], "rows": assessments,
    "limitation": judgments["shared_judgments"]["assessment_status_judgment"]})
print("Independent review and exact source/SDK provenance saved for six requests. Scores remain manual semantic judgments.")
