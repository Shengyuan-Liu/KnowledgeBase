"""Regressions from the first-use PDF acceptance, with no live providers."""
import json
from pathlib import Path

import pytest

from knowledgebase.rag.planning import AnswerRequirement
from knowledgebase.rag.scope import document_references, resolve_document_scope
from knowledgebase.rag.sufficiency import SufficiencyAssessment, validate_assessment
from knowledgebase.schemas import ScopeFile


FIXTURE = json.loads((Path(__file__).parent / "fixtures/new_pdf_scope_failures.json").read_text())


@pytest.mark.parametrize("question", FIXTURE["finance"]["queries"])
def test_recorded_financial_query_keeps_selected_file_scope(question):
    references = document_references(question)
    catalog = [ScopeFile.model_validate(f) for f in FIXTURE["catalog"]]
    scope = resolve_document_scope(references, catalog, file_ids=FIXTURE["finance"]["allowed_file_ids"])
    assert references == []
    assert scope.status == "resolved"
    assert scope.file_ids == FIXTURE["finance"]["allowed_file_ids"]


def test_recorded_invalid_supplement_keeps_supported_and_missing_points():
    recorded = FIXTURE["restricted"]
    decision = SufficiencyAssessment.model_validate_json(recorded["assessment_output"])
    original = decision.model_dump()
    requirements, queries, rejected = validate_assessment(decision,
        [AnswerRequirement.model_validate(r) for r in recorded["requirements"]], recorded["evidence_catalog"])
    assert [r["status"] for r in requirements] == ["supported", "missing"]
    assert all("DPR" in r["quote"] for r in requirements[0]["references"])
    assert requirements[1]["references"] == []
    assert requirements[1]["gap"] == original["requirements"][1]["gap"]
    assert queries == []
    assert rejected == [{"proposal": original["queries"][0],
                         "reason": "Question reformulations cannot contain an unbound target."}]
    assert decision.model_dump() == original


def test_valid_sibling_query_survives_without_repairing_the_rejected_proposal():
    recorded = FIXTURE["restricted"]
    decision = SufficiencyAssessment.model_validate_json(recorded["assessment_output"])
    valid = {"requirement_ids": ["r2"], "query_template": "What negative passages train the retriever?",
             "target": "", "references": []}
    decision.queries.append(type(decision.queries[0]).model_validate(valid))
    _, queries, rejected = validate_assessment(decision,
        [AnswerRequirement.model_validate(r) for r in recorded["requirements"]], recorded["evidence_catalog"])
    assert [q["text"] for q in queries] == [valid["query_template"]]
    assert len(rejected) == 1 and rejected[0]["proposal"]["target"] == ""
