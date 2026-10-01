"""Keep the previously excluded dense table inside its unchanged evidence budget."""

from knowledgebase.rag.retrieval import Retriever

import json
from pathlib import Path

import pytest
import tiktoken

from knowledgebase.config import RetrievalOptions
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.schemas import (
    File, Chunk, ChunkBatch, RetrievedChunk, RetrievalDiagnostics,
)

from knowledgebase.storage.operations import create_file, save_parent_child_chunks, save_pdf_source

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "evals/library-runs/20260927-dense-table-acceptance"
GOLD = ROOT / "evals/check-runs/20260927-dense-table/gold.json"


@pytest.fixture(scope="module")
def dense_inputs():
    document = json.loads((LIVE / "index-snapshot.json").read_text())["files"][0]
    rankings = json.loads((LIVE / "diagnostics/actual-retrieval.json").read_text())
    return document, {row["request"]: row for row in rankings}, json.loads(GOLD.read_text())


def test_table_serialization_preserves_every_coordinate_and_canonical_blank(dense_inputs):
    document, _, gold = dense_inputs
    extraction = File.model_validate({"type": "pdf", **document["extraction"]})
    child = Chunk.model_validate(document["chunks"][0])
    evidence = pdf_evidence(extraction, child.start_offset, child.end_offset)
    item = RetrievedChunk(chunk=child, file_name="background-checks.pdf", distance=0,
                          document_labels=["background-checks"], pdf=evidence)
    before = item.model_dump(mode="json")
    context = build_context([item])

    assert evidence.tables[0].reading in context
    assert item.model_dump(mode="json") == before
    assert f"Excerpt:\n{child.text}\nPDF physical pages: 1" in context
    assert child.text == extraction.text[child.start_offset:child.end_offset]
    assert len(tiktoken.get_encoding("cl100k_base").encode_ordinary(context)) <= 4096
    cells = evidence.tables[0].cells
    for expected in gold["table"]["rows"]:
        label = next(cell for cell in cells if cell[2] == 0 and extraction.text[cell[4]:cell[5]] == expected["label"])
        row = sorted((cell for cell in cells if cell[0] == label[0]), key=lambda cell: cell[2])
        assert [cell[2] for cell in row] == list(range(25))
        assert [extraction.text[cell[4]:cell[5]] for cell in row] == [value or "" for value in expected["values"]]
        assert all(row[column][4] == row[column][5] for column in [16, 17])
    readings = evidence.tables[0].reading.splitlines()
    for expected in gold["table"]["rows"]:
        line = next(line for line in readings if f'"{expected["label"]}"' in line)
        pairs = json.loads(line.split("): ", 1)[1])
        assert pairs == [[" > ".join(path), value if value is not None else {"state": "blank"}] for path, value in
                         zip(gold["table"]["header_paths"][1:], expected["values"][1:], strict=True)]
    alabama = next(line for line in readings if '"Alabama"' in line)
    assert '["Pre-Pawn > Handgun","14"]' in alabama
    assert '["Redemption > Handgun","2,179"]' in alabama
    assert '["Rentals > Handgun",{"state":"blank"}]' in alabama
    assert '["Rentals > Long Gun",{"state":"blank"}]' in alabama
    assert '["Admin","0"]' in alabama
    headers = sorted((cell for cell in cells if cell[0] < label[0] and cell[3] - cell[2] < 25
                      and extraction.text[cell[4]:cell[5]].strip()), key=lambda cell: (cell[0], cell[2]))
    # Restrict to the header rows, before the first annotated state.
    first_row = next(cell[0] for cell in cells if extraction.text[cell[4]:cell[5]] == "Alabama")
    headers = [cell for cell in headers if cell[0] < first_row]
    assert [[" ".join(extraction.text[cell[4]:cell[5]].split()) for cell in headers
             if cell[2] <= column < cell[3]] for column in range(25)] == gold["table"]["header_paths"]


def test_partial_cell_is_not_reported_as_a_complete_value_or_blank(dense_inputs):
    document, _, _ = dense_inputs
    extraction = File.model_validate({"type": "pdf", **document["extraction"]})
    # Start inside Alabama's Handgun value and end inside its Redemption value.
    evidence = pdf_evidence(extraction, 381, 416)
    reading = evidence.tables[0].reading
    assert '"Alabama"' in reading
    assert '["Handgun",' not in reading
    assert '["Redemption > Handgun",' not in reading
    assert '["Pre-Pawn > Handgun","14"]' in reading
    assert 'state' not in reading
    assert any(s.role == "row_header" and s.text == "Alabama" for s in evidence.supplements)


def test_historical_table_snapshot_without_reading_keeps_coordinates(dense_inputs):
    document, _, _ = dense_inputs
    extraction = File.model_validate({"type": "pdf", **document["extraction"]})
    child = Chunk.model_validate(document["chunks"][0])
    evidence = pdf_evidence(extraction, child.start_offset, child.end_offset)
    evidence.tables[0].reading = None
    item = RetrievedChunk(chunk=child, file_name="background-checks.pdf", distance=0, pdf=evidence)
    line = next(line for line in build_context([item]).splitlines() if line.startswith("Table cells ["))
    payload = json.loads(line.split(": ", 1)[1])
    assert payload[0]["cells"] == [list(cell) for cell in evidence.tables[0].cells]


@pytest.mark.parametrize("case_id", ["dense-table", "state-totals"])
@pytest.mark.parametrize("arm", ["single", "planned"])
def test_observed_rankings_supply_target_rows_with_headers_and_page(sessions, dense_inputs, case_id, arm):
    document, rankings, _ = dense_inputs
    extraction = File.model_validate({"type": "pdf", **document["extraction"]})
    identity = document["file"]["file_id"]
    children = {chunk["chunk_id"]: Chunk.model_validate(chunk) for chunk in document["chunks"]}
    with sessions.begin() as session:
        create_file(session, identity, "background-checks.pdf")
        save_pdf_source(session, identity, extraction, indexing={})
        save_parent_child_chunks(session, ChunkBatch(
            parents=[Chunk.model_validate({**parent, "chunk_id": parent["parent_id"], "parent_id": None, "type": "parent"}) for parent in document["parents"]], children=list(children.values())))
    row = rankings[case_id + "-" + arm]
    selected = [RetrievedChunk.model_validate({**hit, "chunk": children[hit["chunk_id"]],
                "file_name": "background-checks.pdf", "document_labels": ["background-checks"]}) for hit in row["candidates"]]
    with sessions() as session:
        packed = Retriever.pack(selected, session, RetrievalDiagnostics(
            max_tokens=4096, tokenizer="cl100k_base", options=RetrievalOptions(packing_strategy="parent_then_child")))
    context = build_context(packed.chunks)
    assert all(value in context for value in ["Alabama", "Alaska", "Arizona", "18,870", "23,022", "22,650", "71,137", "7,095", "27,087", "November - 2015"])
    if case_id == "dense-table":
        assert "They do not represent the number of firearms sold" in context
    target = next(hit for hit in packed.chunks if hit.chunk.chunk_id.endswith(":child:0"))
    assert target.pdf.regions and {region.page_index for region in target.pdf.regions} == {0}
    assert target.pdf.tables[0].cells == pdf_evidence(extraction, target.chunk.start_offset, target.chunk.end_offset).tables[0].cells
    assert all(hit.chunk.text == extraction.text[hit.chunk.start_offset:hit.chunk.end_offset] for hit in packed.chunks)
    assert target.parent_id not in {hit.chunk.chunk_id for hit in packed.chunks}
    assert len(tiktoken.get_encoding("cl100k_base").encode_ordinary(context)) == packed.diagnostics.evidence_tokens <= 4096
    assert packed.diagnostics.context_format == "source-metadata-pdf-v4"
