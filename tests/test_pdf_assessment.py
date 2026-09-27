"""Select financial evidence passages without asking a model to copy table text."""
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.planning import AnswerRequirement
from knowledgebase.rag.sufficiency import (
    SufficiencyAssessment, assessment_context, assessment_excerpts, validate_assessment,
)
from knowledgebase.schemas import RetrievedEvidence, StructuredChunk

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def frozen_pdf_evidence():
    packed = json.loads((ROOT / "evals/check-runs/20260927-pdf-evidence-packing/after-2.json").read_text())
    index = json.loads((ROOT / "evals/library-runs/20260927-v2-pdf-live/index-snapshot.json").read_text())
    documents = {d["file"]["file_id"]: d["extraction"]["text"] for d in index["files"]}
    extractions = {d["file"]["file_id"]: PdfExtraction.model_validate(d["extraction"]) for d in index["files"]}
    chunks = {c["chunk_id"]: c for d in index["files"] for c in d["chunks"]}
    chunks.update({p["parent_id"]: {**p, "chunk_id": p["parent_id"]} for d in index["files"] for p in d["parents"]})
    for row in packed["rows"]:
        evidence = RetrievedEvidence.model_validate(row["result"])
        for hit in evidence.chunks:
            hit.chunk = StructuredChunk.model_validate(chunks[hit.chunk.chunk_id])
            hit.pdf = pdf_evidence(extractions[hit.chunk.file_id], hit.chunk.start_offset, hit.chunk.end_offset)
        row["evidence"] = evidence
    return packed["rows"], documents


@pytest.mark.parametrize("case_id", ["apple-sales", "apple-income", "apparent-conflict"])
@pytest.mark.parametrize("arm", ["single", "planned"])
def test_financial_passages_select_values_headers_units_and_original_page(frozen_pdf_evidence, case_id, arm):
    rows, documents = frozen_pdf_evidence
    row = next(r for r in rows if (r["case_id"], r["arm"]) == (case_id, arm))
    result = SimpleNamespace(evidence=row["evidence"])
    catalog = assessment_excerpts(result)
    amounts = ("14,736", "93,736") if case_id == "apple-income" else ("94,930", "391,035")
    markers = [amounts, ("Three Months Ended",), ("Twelve Months Ended",),
               ("September 28, 2024",), ("In millions",)]
    selected = [next(e for e in catalog if e["source_number"] == 1 and e["page_indices"] == [0]
                     and all(word in e["text"] for word in words)) for words in markers]
    selected = list({e["evidence_id"]: e for e in selected}.values())
    decision = SufficiencyAssessment.model_validate({"requirements": [{
        "requirement_id": "financial", "status": "supported", "gap": "",
        "references": [{"evidence_id": e["evidence_id"]} for e in selected],
    }], "queries": []})
    requirements, _ = validate_assessment(decision,
        [AnswerRequirement(requirement_id="financial", description=row["question"])], catalog)
    references = requirements[0]["references"]
    assert 4 <= len({r["evidence_id"] for r in references}) <= 5
    for reference, passage in zip(references, selected):
        assert reference["quote"] == passage["text"]
        assert reference["quote"] == documents[reference["file_id"]][reference["start_offset"]:reference["end_offset"]]
        assert reference["page_indices"] == [0]
    # These are reviewer-selected IDs, not an assessment of model semantic accuracy.
    assert "quote" not in decision.model_dump()["requirements"][0]["references"][0]


def test_all_frozen_pdf_contexts_keep_metadata_and_only_select_supplied_text(frozen_pdf_evidence):
    rows, documents = frozen_pdf_evidence
    for row in rows:
        result = SimpleNamespace(evidence=row["evidence"])
        catalog = assessment_excerpts(result)
        annotated = assessment_context(result, catalog)
        assert re.sub(r"(?m)^\[p\d+\] ", "", annotated) == row["context"] == build_context(result.evidence.chunks)
        assert len({e["evidence_id"] for e in catalog}) == len(catalog)
        assert len({(e["file_id"], e["start_offset"], e["end_offset"]) for e in catalog}) == len(catalog)
        by_id = {excerpt["evidence_id"]: excerpt for excerpt in catalog}
        for excerpt in catalog:
            assert excerpt["text"] == documents[excerpt["file_id"]][excerpt["start_offset"]:excerpt["end_offset"]]
            hit = result.evidence.chunks[excerpt["source_number"] - 1]
            spans = [(hit.chunk.start_offset, hit.chunk.end_offset),
                     *((s.start_offset, s.end_offset) for s in hit.pdf.supplements)]
            assert any(start <= excerpt["start_offset"] < excerpt["end_offset"] <= end for start, end in spans)
            for link in excerpt.get("table_context", []):
                assert by_id[link["evidence_id"]]["file_id"] == excerpt["file_id"]
                assert link["evidence_id"] != excerpt["evidence_id"]
                assert link["role"] != "row_header"


def test_observed_sales_selection_attaches_periods_without_rewriting_selected_passages(frozen_pdf_evidence):
    rows, documents = frozen_pdf_evidence
    evidence = next(r["evidence"] for r in rows if (r["case_id"], r["arm"]) == ("apple-sales", "planned"))
    catalog = assessment_excerpts(SimpleNamespace(evidence=evidence))
    before = json.loads((ROOT / "evals/library-runs/20260927-financial-acceptance/apple-sales-planned.json").read_text())
    original = before["answer"]["retrieval"]["planning"]["assessment"]["requirements"]
    selected = [{"requirement_id": r["requirement_id"], "status": r["status"], "gap": r["gap"],
                 "references": [{"evidence_id": ref["evidence_id"]} for ref in r["references"]]}
                for r in original]
    decision = SufficiencyAssessment(requirements=selected, queries=[])
    requirements, queries = validate_assessment(decision,
        [AnswerRequirement(requirement_id=r["requirement_id"], description=r["description"]) for r in original], catalog)

    assert decision.model_dump()["requirements"] == selected
    assert queries == []
    for result, previous in zip(requirements, original):
        assert [{k: v for k, v in ref.items() if k != "source_number"} for ref in result["references"]] == previous["references"]
        assert result["status"] == previous["status"]
        assert [ref["evidence_id"] for ref in result["table_context"]] == ["p1", "p2"]
        assert "Three Months Ended\tTwelve Months Ended" in result["table_context"][0]["quote"]
        assert "September 28, 2024\tSeptember 30, 2023" in result["table_context"][1]["quote"]
        for context in result["table_context"]:
            assert context["role"] == "column_header"
            assert context["table_id"] == "#/tables/0"
            assert context["for_evidence_ids"] == ["p6"]
            assert context["source_number"] == 1 and context["page_indices"] == [0]
            assert context["quote"] == documents[context["file_id"]][context["start_offset"]:context["end_offset"]]
    persisted = RetrievedEvidence.model_validate(evidence.model_dump())
    assert persisted.chunks[0].pdf.tables[0].column_header_spans == [
        (170, 188), (189, 208), (209, 227), (228, 246), (247, 265), (266, 284)]


def test_table_context_does_not_expand_source_derived_query_targets(frozen_pdf_evidence):
    rows, _ = frozen_pdf_evidence
    evidence = next(r["evidence"] for r in rows if (r["case_id"], r["arm"]) == ("apple-sales", "planned"))
    catalog = assessment_excerpts(SimpleNamespace(evidence=evidence))
    decision = SufficiencyAssessment(requirements=[{
        "requirement_id": "sales", "status": "partial", "gap": "Find the requested explanation.",
        "references": [{"evidence_id": "p6"}],
    }], queries=[{
        "requirement_ids": ["sales"], "query_template": "Find an explanation for {target}.",
        "target": "94,930", "references": [{"evidence_id": "p6"}],
    }])
    requirements = [AnswerRequirement(requirement_id="sales", description="Explain the reported sales.")]
    normalized, queries = validate_assessment(decision, requirements, catalog)

    assert normalized[0]["table_context"]
    assert [ref["evidence_id"] for ref in queries[0]["references"]] == ["p6"]
    assert "table_context" not in queries[0]
    decision.queries[0].target = "September 28, 2024"
    with pytest.raises(ValueError, match="every selected passage"):
        validate_assessment(decision, requirements, catalog)


def test_separately_supplied_table_headers_are_attached_as_exact_context(frozen_pdf_evidence):
    rows, documents = frozen_pdf_evidence
    evidence = next(r["evidence"] for r in rows if (r["case_id"], r["arm"]) == ("apparent-conflict", "planned"))
    catalog = assessment_excerpts(SimpleNamespace(evidence=evidence))
    row = next(e for e in catalog if "Total net sales" in e["text"] and "94,930" in e["text"])
    normalized, _ = validate_assessment(SufficiencyAssessment(requirements=[{
        "requirement_id": "period", "status": "supported", "gap": "",
        "references": [{"evidence_id": row["evidence_id"]}],
    }], queries=[]), [AnswerRequirement(requirement_id="period", description="Identify the sales periods.")], catalog)

    assert [ref["evidence_id"] for ref in normalized[0]["references"]] == [row["evidence_id"]]
    context = normalized[0]["table_context"]
    assert {ref["quote"] for ref in context if ref["role"] == "column_header"} == {
        "Three Months Ended", "Twelve Months Ended", "September 28, 2024", "September 30, 2023"}
    assert any(ref["role"] == "preceding_text" and "In millions" in ref["quote"] for ref in context)
    for ref in context:
        assert ref["for_evidence_ids"] == [row["evidence_id"]]
        assert ref["quote"] == documents[ref["file_id"]][ref["start_offset"]:ref["end_offset"]]


def test_attached_table_context_cannot_supply_a_second_conflicting_reference(frozen_pdf_evidence):
    rows, _ = frozen_pdf_evidence
    evidence = next(r["evidence"] for r in rows if (r["case_id"], r["arm"]) == ("apple-sales", "planned"))
    catalog = assessment_excerpts(SimpleNamespace(evidence=evidence))
    decision = SufficiencyAssessment(requirements=[{
        "requirement_id": "sales", "status": "supported", "gap": "",
        "references": [{"evidence_id": "p6"}],
    }], queries=[])
    requirements = [AnswerRequirement(requirement_id="sales", description="Compare reported sales.")]
    normalized, _ = validate_assessment(decision, requirements, catalog)
    assert len(normalized[0]["table_context"]) >= 2

    decision.requirements[0].status = "conflicting"
    decision.requirements[0].gap = "The selected passage was marked as conflicting."
    with pytest.raises(ValueError, match="two distinct source quotes"):
        validate_assessment(decision, requirements, catalog)


def test_repeated_unicode_lines_keep_the_selected_occurrence_and_crlf_offsets():
    text = "Repeated café\r\n\r\nRepeated café\r\n"
    result = SimpleNamespace(evidence=SimpleNamespace(chunks=[SimpleNamespace(
        chunk=SimpleNamespace(file_id="text", start_offset=40, end_offset=40 + len(text), text=text),
        file_name="notes.txt", pdf=None)]))
    catalog = assessment_excerpts(result)
    assert len(catalog) == 2 and catalog[0]["text"] == catalog[1]["text"] == "Repeated café\r\n"
    requirements, _ = validate_assessment(SufficiencyAssessment(requirements=[{
        "requirement_id": "repeat", "status": "supported", "gap": "",
        "references": [{"evidence_id": catalog[1]["evidence_id"]}],
    }], queries=[]), [AnswerRequirement(requirement_id="repeat", description="Second occurrence")], catalog)
    reference = requirements[0]["references"][0]
    assert reference["start_offset"] == 40 + len("Repeated café\r\n\r\n")
    assert reference["end_offset"] == 40 + len(text)
    assert "page_indices" not in reference
