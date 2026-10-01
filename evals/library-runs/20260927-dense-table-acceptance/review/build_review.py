"""Serialize the primary Codex review; scores below are manual judgments.

This reads frozen local artifacts only. It does not call a model, rerun a request,
or use substring matches as semantic scores. Outputs are created exclusively.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
RUN = OUT.parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


frozen = read(RUN / "frozen-cases.json")
snapshot = read(RUN / "index-snapshot.json")["files"][0]
canonical = snapshot["extraction"]["text"]
observations = [
    (line, json.loads(text))
    for line, text in enumerate((RUN / "server-observations.jsonl").read_text().splitlines(), 1)
]
sdk_inputs = {}
for line, event in observations:
    if event["kind"] == "sdk_start" and event.get("api") == "responses":
        sdk_inputs.setdefault(event["request"], []).append((line, event))

rows = []
for case in frozen["cases"]:
    for arm in ("single", "planned"):
        name = f"{case['id']}-{arm}"
        artifact = RUN / f"{name}.json"
        raw = read(artifact)
        answer = raw["answer"]
        sources = answer["sources"]
        generation = [
            (line, event) for line, event in sdk_inputs.get(name, [])
            if event["input"].get("stream")
        ]
        source_provenance = [
            {key: source[key] for key in (
                "source_id", "file_id", "file_name", "chunk_id",
                "start_offset", "end_offset",
            )} | {
                "source_hash": source["pdf"]["source_hash"],
                "revision_id": source["pdf"]["revision_id"],
                "page_indices": sorted({r["page_index"] for r in source["pdf"]["regions"]}),
                "tables": source["pdf"]["tables"],
                "supplements": source["pdf"]["supplements"],
            }
            for source in sources
        ]
        row = {
            "pass_name": "dense_table_acceptance",
            "case_id": case["id"],
            "arm": arm,
            "answer_status": raw["status"],
            "source_artifact": f"../{name}.json",
            "source_artifact_sha256": digest(artifact),
            "actual_answer": answer["answer"],
            "generation_sdk_inputs": [
                {
                    "artifact": "../server-observations.jsonl",
                    "line": line,
                    "call_id": event["call_id"],
                    "user_message": next(m["content"] for m in event["input"]["input"] if m["role"] == "user"),
                }
                for line, event in generation
            ],
            "source_provenance": source_provenance,
            "points": [],
            "factual_claim_groups": [],
            "missing_point_review": [],
            "excluded_framing": [],
            "relevance": 0 if case["id"] == "grouped-and-blank-cells" else 1,
            "full_abstention": case["id"] == "grouped-and-blank-cells" or (case["id"] == "state-totals" and arm == "planned"),
            "appropriate_abstention": None,
            "appropriate_abstention_status": "not_applicable: all three frozen questions are answerable from the original page",
            "incorrect_abstention": int(case["id"] == "grouped-and-blank-cells" or (case["id"] == "state-totals" and arm == "planned")),
        }
        if case["id"] == "dense-table":
            row["note"] = "The disclaimer is correct and supported. Four table facts are omitted. The exact SDK user input contains only child 7 disclaimer prose, so the point-specific limitations are faithful to supplied evidence; they do not receive original-page correctness or completeness credit. This is a partial answer, not full abstention."
            point_note = "No Alabama row, relevant value, reporting-period header or table cell metadata is present in the sole supplied excerpt, canonical 4907:5738. The fresh extraction contains the fact, but retrieval candidates are not generation evidence."
        elif case["id"] == "state-totals" and arm == "single":
            row["note"] = "All three emitted totals are wrong against the original page and unsupported by source 1. The exact SDK input contains only disclaimer prose, with no state row or numeric total. Each bullet has a valid citation ID but none has a supporting citation. The response directly addresses the requested states, so relevance is 1 independently of correctness."
            point_note = "The answer substitutes a wrong total. Neither the correct nor emitted total appears in the actual supplied disclaimer excerpt, which has no table rows or cells."
        elif case["id"] == "state-totals":
            row["note"] = "The application returned a full insufficient-evidence refusal with an empty supplied context, without a generation call. This is an honest statement about that empty context but incorrect question-level abstention on an original-page-answerable question. No factual answer claim group is available for faithfulness or citation scoring. Relevance is 1 because the refusal addresses evidence sufficiency for the requested question."
            point_note = "No source excerpt was retained. The application-generated refusal does not answer the requested total. Candidate retrieval and fresh extraction are not supplied evidence."
        else:
            row["note"] = "Document scope resolution treats the reference as background-checks.pdf\" for November 2015 and returns a refusal before retrieval or generation. The actual background-checks.pdf is ready in index-snapshot.json. This operational refusal is not a substantive answer or a demonstrated blank-cell uncertainty judgment. Relevance is 0 because the requested table distinctions are not addressed and the user is incorrectly directed to select/upload a ready file."
            point_note = "Scope resolution returned no source, and no model generated an answer. The requested table fact is omitted. Blank cells are not zero; neither interpretation was exercised in this live request."
        for fact_id in case["expected_fact_ids"]:
            success = int(fact_id == "checks_not_sales")
            row["points"].append({
                "fact_id": fact_id,
                "reference_correctness": success,
                "completeness": success,
                "supplied_evidence_coverage": success,
                "source_ids_with_matching_anchors": [1] if success else [],
                "evidence_note": (
                    "Source 1, physical page 1, canonical 5449:5738 explicitly says these are NICS background checks, not firearms sold, and that there is no one-to-one correlation. Both required clauses occur in the answer and are cited on the same bullet."
                    if success else point_note
                ),
                "reference_fact": frozen["facts"][fact_id],
            })
        bullets = [text[2:] for text in answer["answer"].splitlines() if text.startswith("- ")]
        if case["id"] == "dense-table":
            claim = bullets[0] if arm == "single" else bullets[-1]
            row["factual_claim_groups"].append({
                "text": claim,
                "original_page_correctness": 1,
                "context_support": 1,
                "cited_source_ids": [1],
                "citation_support": 1,
                "citation_coverage": 1,
                "supporting_evidence_artifact": f"../{name}.json#answer.sources[0]",
                "supporting_span": {"start_offset": 5449, "end_offset": 5738, "page_index": 0},
                "note": "All material assertions in this bullet are directly supported by the final disclaimer paragraph in the exact supplied source.",
            })
            limitations = [bullets[1]] if arm == "single" else bullets[:4]
            for i, text in enumerate(limitations):
                row["missing_point_review"].append({
                    "text": text,
                    "fact_ids": case["expected_fact_ids"][:4] if arm == "single" else [case["expected_fact_ids"][i]],
                    "appropriate_to_actual_supplied_context": True,
                    "original_page_complete": False,
                    "cited_source_ids": [1] if arm == "single" else [],
                    "note": "This explicitly limits the claim to the provided excerpt(s), which contain no state values. Scored separately from factual answer groups under the frozen rubric. It does not show that the document itself lacks the values.",
                })
        elif case["id"] == "state-totals" and arm == "single":
            for text, fact_id in zip(bullets, case["expected_fact_ids"]):
                row["factual_claim_groups"].append({
                    "text": text,
                    "original_page_correctness": 0,
                    "context_support": 0,
                    "cited_source_ids": [1],
                    "citation_support": 0,
                    "citation_coverage": 0,
                    "supporting_evidence_artifact": f"../{name}.json#answer.sources[0]",
                    "note": f"Original-page reference: {frozen['facts'][fact_id]['expected']} Source 1 has only prose notes/disclaimer and establishes no total for this state.",
                })
            row["excluded_framing"].append({
                "text": answer["answer"].splitlines()[0],
                "reason": "Introductory restatement of the requested table, month and document; the three numeric bullet claims below are the distinct scored factual groups. This is not counted as a separate repeated factual group.",
            })
        else:
            row["missing_point_review"].append({
                "text": answer["answer"],
                "fact_ids": case["expected_fact_ids"],
                "appropriate_to_actual_supplied_context": case["id"] == "state-totals",
                "original_page_complete": False,
                "cited_source_ids": [],
                "note": "No source context and no generation call. Empty-context insufficiency is faithful, but the grouped-case file-readiness claim is contradicted by the ready snapshot; neither is a substantive table answer. These refusals have no factual answer-group denominator.",
            })
        saved_sources = raw["saved_message"]["sources"]
        row["history_contract_review"] = {
            "raw_history_matches": raw["history_matches"],
            "raw_history_sources_match": raw["history_sources_match"],
            "raw_history_retrieval_matches": raw["history_retrieval_matches"],
            "source_count_match": len(sources) == len(saved_sources),
            "common_source_fields_match": len(sources) == len(saved_sources) and all(
                original == {key: saved[key] for key in original}
                for original, saved in zip(sources, saved_sources)
            ),
            "history_only_source_fields": [
                {key: value for key, value in saved.items() if key not in original}
                for original, saved in zip(sources, saved_sources)
            ],
            "note": "Raw source equality is retained unchanged. For source-bearing answers, history adds file_deleted=false; all common source fields, answer and retrieval metadata match. This is a schema addition, not lost or changed evidence.",
        }
        rows.append(row)

review = {
    "reviewer": "Codex model reviewer /root/table_reference_context; no human or paid judge",
    "reviewed_at": datetime.now(timezone.utc).isoformat(),
    "code_version": frozen["code_version"],
    "rubric": "../protocol.md; frozen 0 / 0.5 / 1 requested-point scores and factual paragraph/bullet groups. Missing-information claims and operational refusals are separate. No claim-free response receives a faithfulness or citation denominator.",
    "review_scope": "All six raw answers, all three actual generation SDK user inputs, both actual evidence-assessment SDK inputs/outputs, the ready fresh-index snapshot, source identities, and original-page gold. No provider calls or production edits performed by this review.",
    "independence": "Primary raw-answer and SDK-context judgments were made without opening root-review.json. Root later disclosed the matching aggregate outcome before this file was serialized; row-level relevance, evidence notes and reference audits were completed independently. Reconciliation is retained in a separate file.",
    "facts_artifact": "../frozen-cases.json",
    "facts_sha256": digest(RUN / "frozen-cases.json"),
    "original_page_artifact": "../../20260927-v2-pdf-live/source-review/background-checks-1.png",
    "original_page_sha256": frozen["source_annotations"]["original_page_sha256"],
    "original_page_review": "The original page was visually inspected during the earlier native-probe review; this review uses the same unchanged source-bound gold and page artifact. No new browser page click is claimed.",
    "source_hash": frozen["corpus"][0]["sha256"],
    "extraction_revision_id": snapshot["extraction"]["revision_id"],
    "sdk_artifact": "../server-observations.jsonl",
    "sdk_artifact_sha256": digest(RUN / "server-observations.jsonl"),
    "grouping_decisions": [
        "The two complete disclaimer bullets are two factual claim groups. The three state-total bullets are three more. All five have inline citation [1], but only the two disclaimer groups have supporting citations.",
        "The dense-table limitations are explicit claims about supplied excerpts, not numerical table answers. They are retained separately, receive no requested table-point credit, and do not inflate faithfulness/citation denominators.",
        "The three application refusals have no substantive factual answer group. They count as incorrect full abstention on answerable questions and remain visible as operational outcomes.",
        "Relevance measures whether the response addresses the question independently of accuracy: the wrong state totals are on topic; the empty-context refusal addresses question sufficiency; the malformed-file refusals instead direct the user away from an already-ready document and score zero.",
    ],
    "blank_cell_review": {
        "status": "unavailable",
        "reason": "Both grouped/blank requests stop at filename scope resolution. No model sees or answers either blank cell. This run cannot establish live blank interpretation, parent-header association, or automatic table-context effectiveness.",
        "observable_evidence_required": frozen["blank_evidence_rule"],
        "no_blank_as_zero_claims_emitted": True,
        "absence_of_error_is_not_success": True,
    },
    "baseline_comparison": {
        "artifact": "../../20260927-v2-pdf-live/reviewed-cases.json",
        "pass_name": "repair",
        "historical_scores_preserved": True,
        "matched_case_id": "dense-table",
        "single": "Requested correctness/completeness and supplied evidence remain 1/5. The old single response fabricated four Alabama values; the new single response accurately limits itself to the supplied excerpt and answers only the disclaimer. Factual-group denominator changes from five (one supported) to one (supported), so a percentage alone would obscure remaining incompleteness.",
        "planned": "Requested correctness/completeness and supplied evidence remain 1/5. Both old and current responses omit four values and answer the supported disclaimer; one supported factual group in each.",
        "new_cases": "state-totals and grouped-and-blank-cells have no historical matched live baseline.",
        "comparability_limits": frozen["historical_comparison"]["comparability_note"],
    },
    "rows": rows,
}
save("reviewed-cases.json", review)

assessment_rows = []
for case in frozen["cases"]:
    name = f"{case['id']}-planned"
    raw = read(RUN / f"{name}.json")
    planning = raw["answer"]["retrieval"]["planning"]
    assessments = planning.get("hops", {}).get("assessments", [])
    if not assessments and planning.get("assessment"):
        assessments = [planning["assessment"]]
    for assessment in assessments:
        record = assessment["record"]
        decision = json.loads(record["output_text"]) if record else None
        normalized = assessment["requirements"]
        raw_requirements = {r["requirement_id"]: r for r in decision["requirements"]} if decision else {}
        entries = []
        for requirement in normalized:
            raw_requirement = raw_requirements.get(requirement["requirement_id"])
            refs = requirement["references"]
            entries.append({
                "requirement_id": requirement["requirement_id"],
                "description": requirement["description"],
                "status": requirement["status"],
                "gap": requirement["gap"],
                "raw_model_selected_references": raw_requirement["references"] if raw_requirement else None,
                "normalized_references": refs,
                "application_added_table_context": requirement["table_context"],
                "selected_ids_preserved": (
                    [r["evidence_id"] for r in raw_requirement["references"]] == [r["evidence_id"] for r in refs]
                    if raw_requirement else None
                ),
                "exact_reference_spans_preserved": all(canonical[r["start_offset"]:r["end_offset"]] == r["quote"] for r in refs),
                "status_supported_by_actual_assessment_context": True,
                "note": (
                    "p4 is the exact NICS checks/not-sales/no-one-to-one disclaimer on physical page 1 at 5449:5738. It lies inside current generation source 1 (4907:5738). No table context is attached and no source number remapping is needed."
                    if refs else "Missing is accurate for this supplied context; it does not assert that the original PDF is missing the fact. No selected reference is silently filled by the application."
                ),
            })
        calls = [
            {"artifact": "../server-observations.jsonl", "line": line, "call_id": event["call_id"]}
            for line, event in sdk_inputs.get(name, [])
            if event["input"].get("text", {}).get("format", {}).get("name") == "evidence_assessment"
        ]
        assessment_rows.append({
            "case_id": case["id"],
            "arm": "planned",
            "round_index": assessment["round_index"],
            "origin": "provider_assessment" if record else "application_empty_context_assessment",
            "source_artifact": f"../{name}.json#answer.retrieval.planning.hops.assessments",
            "sdk_input": calls[assessment["round_index"] - 1] if record else None,
            "raw_model_decision": decision,
            "requirements": entries,
            "table_context_effectiveness": "not_applicable: no table passages were supplied or selected",
            "supplementary_query_review": (
                "Round 1 reformulates only original question concepts, keeps the literal original filename/month, target='', and no source-derived references. Round 2 has no remaining query budget and proposes no query. Neither invents a source-derived target."
                if case["id"] == "dense-table" else "No provider assessment or supplementary query; context was empty."
            ),
        })
    if not assessments:
        assessment_rows.append({
            "case_id": case["id"], "arm": "planned", "round_index": None,
            "origin": "no_assessment_scope_unresolved",
            "source_artifact": f"../{name}.json#answer.retrieval",
            "requirements": [],
            "note": "Scope resolution failed before retrieval, assessment or generation. This is not evidence that the model understood grouped headers or blank cells.",
        })

save("assessment-reference-review.json", {
    "reviewer": review["reviewer"],
    "reviewed_at": review["reviewed_at"],
    "code_version": frozen["code_version"],
    "scope": "Both actual dense-table assessment calls, the synthetic empty-context state assessment, and grouped-case no-assessment path. Model-selected IDs, exact raw spans, application additions, and final generation citation IDs are distinguished.",
    "rows": assessment_rows,
    "limitation": "All live table-context/header/blank association paths are unexercised because no table evidence reaches an assessor or generator. Exact selected disclaimer spans are sound; this does not establish dense-table task success.",
})
print(json.dumps({"saved": ["reviewed-cases.json", "assessment-reference-review.json"], "rows": len(rows), "requested_points": sum(len(r["points"]) for r in rows), "factual_claim_groups": sum(len(r["factual_claim_groups"]) for r in rows)}))
