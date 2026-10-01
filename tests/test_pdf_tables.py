"""Recover the observed collapsed native table against original-page gold labels."""

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("docling", reason="Install the pdf extra to run PDF table tests.")
pytest.importorskip("pdfplumber", reason="Install the pdf extra to run PDF table tests.")

from docling_core.types.doc import DoclingDocument

from knowledgebase.rag.chunking import split_parent_child
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf import adapt_pdf_document
from knowledgebase.rag.pdf_evidence import pdf_evidence, table_rows
from knowledgebase.schemas import (
    PdfParserIdentity, RetrievedChunk,
)
from knowledgebase.rag.pdf_tables import recover_collapsed_tables


ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "evals/check-runs/20260926-pdf-parser-selection"
MATERIALS = ROOT / "evals/materials/pdf-v2"
GOLD = json.loads((ROOT / "evals/check-runs/20260927-dense-table/gold.json").read_text())
IDENTITY = PdfParserIdentity(package_versions=(("docling", "2.130.0"),),
    settings_json='{"do_ocr":false}', model_file_hashes=())


def normalized(text):
    return " ".join(text.split())


def row_cells(table, label):
    row = next(cell.row_start for cell in table.cells
               if cell.column_start == 0 and normalized(cell.text) == label)
    return sorted((cell for cell in table.cells if cell.row_start == row),
                  key=lambda cell: cell.column_start)


def header_paths(table, first_data_row):
    # Full-width title/date cells supply context, not another column-path level.
    headers = sorted((cell for cell in table.cells
        if cell.column_header and cell.row_start < first_data_row
        and cell.column_end - cell.column_start < table.columns and normalized(cell.text)),
        key=lambda cell: (cell.row_start, cell.column_start))
    return [[normalized(cell.text) for cell in headers
             if cell.column_start <= column < cell.column_end]
            for column in range(table.columns)]


@pytest.fixture(scope="module")
def recovered_pdf():
    document = DoclingDocument.model_validate_json(
        (SELECTION / "attempt-1/background-checks-docling.json").read_text())
    source = (MATERIALS / "background-checks.pdf").read_bytes()
    assert document.tables[0].data.num_rows == document.tables[0].data.num_cols == 1
    before = adapt_pdf_document(document, source, IDENTITY)

    recovered = recover_collapsed_tables(document, source)
    after = adapt_pdf_document(document, source, IDENTITY)
    table = next(block.table for block in after.blocks if block.table)
    return SimpleNamespace(before=before, after=after, table=table,
                           recovered=recovered, source=source)


def test_observed_missing_alabama_values_are_recovered_in_a_new_revision(recovered_pdf):
    result = recovered_pdf
    expected = [fact["exact_value"] for fact in GOLD["original_question"]["table_facts"]]
    assert all(value not in result.before.text for value in expected)
    assert all(value in result.after.text for value in expected)
    assert result.recovered == ("#/tables/0",)
    assert result.before.source_hash == result.after.source_hash == GOLD["source"]["sha256"]
    assert result.after.source_hash == sha256(result.source).hexdigest()
    assert result.before.revision_id != result.after.revision_id
    assert result.before.extraction_hash != result.after.extraction_hash


@pytest.mark.parametrize("expected", GOLD["table"]["rows"], ids=lambda row: row["label"])
def test_complete_state_rows_keep_column_associations_and_explicit_blanks(recovered_pdf, expected):
    cells = row_cells(recovered_pdf.table, expected["label"])

    assert len(cells) == GOLD["table"]["column_count"]
    assert [cell.column_start for cell in cells] == list(range(25))
    assert all(cell.column_end == cell.column_start + 1 for cell in cells)
    assert all(cell.row_end == cell.row_start + 1 for cell in cells)
    assert [normalized(cell.text) for cell in cells] == [value or "" for value in expected["values"]]
    # These visible blanks must retain their two Rentals positions, not become zero.
    for column, path in enumerate(GOLD["table"]["header_paths"]):
        if path[0] == "Rentals":
            assert cells[column].text == ""
            assert cells[column].start_offset == cells[column].end_offset


def test_complete_header_paths_retain_six_merged_groups(recovered_pdf):
    table = recovered_pdf.table
    first_data_row = row_cells(table, "Alabama")[0].row_start

    assert table.columns == GOLD["table"]["column_count"]
    assert header_paths(table, first_data_row) == GOLD["table"]["header_paths"]
    groups = sorted((cell for cell in table.cells if cell.column_header and normalized(cell.text)
                     and 1 < cell.column_end - cell.column_start < table.columns),
                    key=lambda cell: cell.column_start)
    assert [(normalized(cell.text), cell.column_start, cell.column_end) for cell in groups] == [
        (group["label"], group["column_start"], group["column_end"])
        for group in GOLD["table"]["merged_header_groups"]
    ]
    assert len({(cell.row_start, cell.row_end) for cell in groups}) == 1


def test_recovered_cells_keep_exact_canonical_slices_and_physical_cell_boxes(recovered_pdf):
    extraction, table = recovered_pdf.after, recovered_pdf.table
    page = extraction.pages[0]
    assert extraction.page_count == 1
    for cell in table.cells:
        assert extraction.text[cell.start_offset:cell.end_offset] == cell.text
        assert len(cell.regions) == 1
        region = cell.regions[0]
        assert region.page_index == 0
        assert region.precision == "cell"
        assert (region.start_offset, region.end_offset) == (cell.start_offset, cell.end_offset)
        left, top, right, bottom = region.bbox
        assert 0 <= left < right <= page.width
        assert 0 <= top < bottom <= page.height

    row_centers = []
    for expected in GOLD["table"]["rows"]:
        cells = row_cells(table, expected["label"])
        centers = [(cell.regions[0].bbox[0] + cell.regions[0].bbox[2]) / 2 for cell in cells]
        assert all(left < right for left, right in zip(centers, centers[1:]))
        box = cells[0].regions[0].bbox
        row_centers.append((box[1] + box[3]) / 2)
    assert all(top < bottom for top, bottom in zip(row_centers, row_centers[1:]))


def test_title_date_and_background_check_disclaimer_survive(recovered_pdf):
    text = normalized(recovered_pdf.after.text)
    for control in GOLD["document_controls"]:
        if "expected_text" in control:
            assert normalized(control["expected_text"]) in text
        else:
            assert all(normalized(phrase) in text for phrase in control["required_phrases"])


@pytest.mark.parametrize("name", ["doclaynet", "ml-lecture", "docling-report", "apple-fy24"])
def test_other_frozen_corpus_documents_are_unchanged(name):
    folder = "apple-1" if name == "apple-fy24" else "attempt-1"
    document = DoclingDocument.model_validate_json((SELECTION / folder / f"{name}-docling.json").read_text())
    source = (MATERIALS / f"{name}.pdf").read_bytes()
    original = document.model_dump(mode="json")
    before = adapt_pdf_document(document, source, IDENTITY)

    recovered = recover_collapsed_tables(document, source)

    assert recovered == ()
    assert document.model_dump(mode="json") == original
    assert adapt_pdf_document(document, source, IDENTITY) == before


def test_alabama_child_keeps_exact_values_headers_and_title_on_page_one(recovered_pdf):
    extraction, table = recovered_pdf.after, recovered_pdf.table
    cells = row_cells(table, "Alabama")
    start, end = min(cell.start_offset for cell in cells), max(cell.end_offset for cell in cells)
    hierarchy = split_parent_child(extraction.text, extraction.source_blocks(), "background",
        parent_max_tokens=768, child_max_tokens=128, encoding_name="cl100k_base",
        table_row_spans=table_rows(extraction))
    child = next(chunk for chunk in hierarchy.children
                 if chunk.start_offset <= start and end <= chunk.end_offset)
    evidence = pdf_evidence(extraction, child.start_offset, child.end_offset)
    hit = RetrievedChunk(file_name="background-checks.pdf", chunk=child, distance=0.1, pdf=evidence)
    context = normalized(build_context([hit]))

    assert child.text == extraction.text[child.start_offset:child.end_offset]
    assert all(fact["exact_value"] in child.text for fact in GOLD["original_question"]["table_facts"])
    assert all(normalized(label) in context for path in GOLD["table"]["header_paths"] for label in path)
    assert "NICS Firearm Background Checks" in context
    assert "November - 2015" in context
    assert any(supplement.role == "column_header" for supplement in evidence.supplements)
    assert {region.page_index for region in evidence.regions} == {0}
    for supplement in evidence.supplements:
        assert supplement.text == extraction.text[supplement.start_offset:supplement.end_offset]
        assert {region.page_index for region in supplement.regions} == {0}
    supplied_cells = {tuple(cell) for item in evidence.tables for cell in item.cells}
    assert all((cell.row_start, cell.row_end, cell.column_start, cell.column_end,
                cell.start_offset, cell.end_offset) in supplied_cells
               for cell in table.cells if cell.column_header)
