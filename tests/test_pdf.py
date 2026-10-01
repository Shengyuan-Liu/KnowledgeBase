"""PDF contracts use frozen real parser output; unit tests never download models."""

from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

pytest.importorskip("docling", reason="Install the pdf extra to run PDF adapter tests.")

from docling.datamodel.base_models import ConversionStatus
from docling_core.types.doc import (
    BoundingBox, DocItemLabel, DoclingDocument, ProvenanceItem, Size, TableCell, TableData,
)

from knowledgebase.rag.pdf import PdfParser, adapt_pdf_document
from knowledgebase.schemas import PdfExtraction, PdfParserIdentity


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "evals/check-runs/20260926-pdf-parser-selection/attempt-1"
IDENTITY = PdfParserIdentity(package_versions=(("docling", "2.130.0"),),
                             settings_json='{"do_ocr":false}', model_file_hashes=())


def provenance(page, start, end):
    return ProvenanceItem(page_no=page, charspan=(start, end),
                          bbox=BoundingBox(l=10, t=90, r=90, b=60, coord_origin="BOTTOMLEFT"))


def document():
    doc = DoclingDocument(name="fixture")
    doc.add_page(page_no=1, size=Size(width=100, height=100))
    doc.add_page(page_no=2, size=Size(width=100, height=100))
    return doc


@pytest.mark.parametrize("name", ["doclaynet", "ml-lecture", "docling-report", "background-checks"])
def test_frozen_documents_preserve_exact_slices_and_regions(name):
    doc = DoclingDocument.model_validate_json((FROZEN / f"{name}-docling.json").read_text())
    source = (ROOT / f"evals/materials/pdf-v2/{name}.pdf").read_bytes()
    result = adapt_pdf_document(doc, source, IDENTITY)
    assert result.source_hash == sha256(source).hexdigest()
    assert result.extraction_hash == sha256(result.text.encode()).hexdigest()
    assert PdfExtraction.model_validate_json(result.model_dump_json()) == result
    assert result == adapt_pdf_document(doc, source, IDENTITY)
    previous_end = 0
    pages = {p.page_index: p for p in result.pages}
    for block in result.blocks:
        assert block.start_offset >= previous_end
        assert block.text == result.text[block.start_offset:block.end_offset]
        assert not result.text[previous_end:block.start_offset].strip()
        previous_end = block.end_offset
        for r in block.regions:
            assert block.start_offset <= r.start_offset <= r.end_offset <= block.end_offset
            assert 0 <= r.bbox[0] <= r.bbox[2] <= pages[r.page_index].width
            assert 0 <= r.bbox[1] <= r.bbox[3] <= pages[r.page_index].height
        if block.table:
            for cell in block.table.cells:
                assert cell.text == result.text[cell.start_offset:cell.end_offset]
    assert not result.text[previous_end:].strip()


def test_cross_page_regions_retain_physical_indices_and_partial_span_precision():
    doc = document()
    item = doc.add_text(label=DocItemLabel.TEXT, text="First page. Second page.", prov=provenance(1, 0, 11))
    item.prov.append(provenance(2, 12, 24))
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    assert [r.page_index for r in result.locate(0, len(result.text))] == [0, 1]
    assert result.locate(2, 5)[0].bbox == (10, 10, 90, 40)
    assert result.locate(2, 5)[0].precision == "block"
    assert result.locate(12, 18)[0].page_index == 1
    assert result.locate(11, 12) == ()  # Synthetic space has no original-page box.
    assert result.locate(0, 0) == ()
    with pytest.raises(ValueError):
        result.locate(-1, 2)


def test_cross_page_real_paragraph_maps_to_both_original_pages():
    doc = DoclingDocument.model_validate_json((FROZEN / "docling-report-docling.json").read_text())
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    block = next(b for b in result.blocks if b.text.startswith("Establishing GPU"))
    assert [r.page_index for r in block.regions] == [3, 4]
    assert len(result.locate(block.start_offset, block.end_offset)) == 2


def test_real_list_markers_are_retained_in_the_provenance_coordinate_space():
    doc = DoclingDocument.model_validate_json((FROZEN / "doclaynet-docling.json").read_text())
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    block = next(b for b in result.blocks if "Human Annotation:" in b.text)
    assert block.text.startswith("(1) Human Annotation:")
    assert block.regions[0].end_offset == block.end_offset


def test_real_financial_table_retains_period_headers_values_and_units():
    path = FROZEN.parent / "apple-1/apple-fy24-docling.json"
    doc = DoclingDocument.model_validate_json(path.read_text())
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    table = next(b.table for b in result.blocks if b.table)
    cells = {(c.row_start, c.column_start): c for c in table.cells}
    assert cells[0, 1].text == "Three Months Ended"
    assert cells[0, 1].column_end == 3
    assert cells[0, 3].text == "Twelve Months Ended"
    assert cells[5, 0].text == "Total net sales (1)"
    assert cells[5, 1].text == "94,930"
    assert cells[5, 3].text == "391,035"
    assert "In millions" in result.text


def test_table_cells_are_serialized_once_with_header_and_merged_spans():
    doc = document()
    table = doc.add_table(data=TableData(num_rows=2, num_cols=2, table_cells=[
        TableCell(text="Quarter", start_row_offset_idx=0, end_row_offset_idx=1,
                  start_col_offset_idx=0, end_col_offset_idx=2, col_span=2, column_header=True),
        TableCell(text="A", start_row_offset_idx=1, end_row_offset_idx=2,
                  start_col_offset_idx=0, end_col_offset_idx=1, row_header=True),
        TableCell(text="42", start_row_offset_idx=1, end_row_offset_idx=2,
                  start_col_offset_idx=1, end_col_offset_idx=2,
                  bbox=BoundingBox(l=50, t=20, r=90, b=40, coord_origin="TOPLEFT")),
    ]), prov=provenance(1, 0, 0))
    caption = doc.add_text(label=DocItemLabel.CAPTION, text="Table 1. Units: USD", prov=provenance(1, 0, 19))
    table.captions.append(caption.get_ref())
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    block = next(b for b in result.blocks if b.table)
    assert block.text == "Quarter\nA\t42"
    assert block.table.cells[0].column_end == 2
    assert block.table.cells[0].column_header
    assert block.table.cells[1].row_header
    assert block.table.cells[2].regions[0].precision == "cell"
    assert block.table.caption_refs == (caption.self_ref,)
    assert block.regions[0].precision == "table"
    assert "table_structure_unverified" in {w.code for w in result.warnings}


def test_omissions_blank_pages_and_formula_limitations_are_explicit():
    doc = document()
    doc.add_picture(prov=provenance(1, 0, 0))
    doc.add_text(label=DocItemLabel.FORMULA, text="x = 1", prov=provenance(1, 0, 5))
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    warnings = {w.code: w for w in result.warnings}
    assert warnings["picture_not_interpreted"].page_indices == (0,)
    assert "formula_not_understood" in warnings
    assert warnings["no_extracted_text"].page_indices == (1,)
    assert result.pages[0].printed_label is None


def test_revisions_and_nested_records_are_immutable_and_chunker_copies_are_independent():
    doc = document()
    doc.add_text(label=DocItemLabel.TEXT, text="Text", prov=provenance(1, 0, 4))
    result = adapt_pdf_document(doc, b"pdf", IDENTITY)
    for obj, field, value in [(result, "text", "changed"), (result.blocks[0], "text", "changed"),
                              (result.pages[0], "width", 99)]:
        with pytest.raises(ValidationError):
            setattr(obj, field, value)
    copies = result.source_blocks()
    copies[0].text = "Changed"
    assert result.text == "Text"
    changed = adapt_pdf_document(doc, b"different original", IDENTITY)
    assert changed.extraction_hash == result.extraction_hash
    assert changed.revision_id != result.revision_id
    changed_settings = IDENTITY.model_copy(update={"settings_json": "{}"})
    assert adapt_pdf_document(doc, b"pdf", changed_settings).revision_id != result.revision_id


def test_parser_disables_deferred_features_and_rejects_partial_conversion(tmp_path, monkeypatch):
    (tmp_path / "model.bin").write_bytes(b"unit-test model identity")
    factory = Mock()
    monkeypatch.setattr("knowledgebase.rag.pdf.DocumentConverter", factory)
    parser = PdfParser(tmp_path)
    settings = json.loads(parser.identity.settings_json)
    for name in ["do_ocr", "do_formula_enrichment", "do_picture_description", "do_chart_extraction",
                 "enable_remote_services"]:
        assert settings[name] is False
    assert parser.identity.model_file_hashes[0][1] == sha256(b"unit-test model identity").hexdigest()
    factory.return_value.convert.return_value = Mock(status=ConversionStatus.PARTIAL_SUCCESS, errors=["incomplete"])
    with pytest.raises(ValueError, match="did not complete"):
        parser.parse(b"pdf")
    doc = document()
    factory.return_value.convert.return_value = Mock(status=ConversionStatus.SUCCESS, document=doc)
    result = parser.parse(b"pdf")
    assert result.page_count == 2
    assert result.text == ""
    assert sum(w.code == "no_extracted_text" for w in result.warnings) == 2
