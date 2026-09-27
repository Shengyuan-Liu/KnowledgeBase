"""Select financial evidence passages without asking a model to copy table text."""
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from knowledgebase.rag.context import build_context
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
    chunks = {c["chunk_id"]: c for d in index["files"] for c in d["chunks"]}
    chunks.update({p["parent_id"]: {**p, "chunk_id": p["parent_id"]} for d in index["files"] for p in d["parents"]})
    for row in packed["rows"]:
        evidence = RetrievedEvidence.model_validate(row["result"])
        for hit in evidence.chunks:
            hit.chunk = StructuredChunk.model_validate(chunks[hit.chunk.chunk_id])
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
        for excerpt in catalog:
            assert excerpt["text"] == documents[excerpt["file_id"]][excerpt["start_offset"]:excerpt["end_offset"]]
            hit = result.evidence.chunks[excerpt["source_number"] - 1]
            spans = [(hit.chunk.start_offset, hit.chunk.end_offset),
                     *((s.start_offset, s.end_offset) for s in hit.pdf.supplements)]
            assert any(start <= excerpt["start_offset"] < excerpt["end_offset"] <= end for start, end in spans)


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
