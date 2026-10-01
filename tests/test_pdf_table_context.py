"""Adjacent table context from the PDFs observed in live acceptance."""

import json
from pathlib import Path

import pytest

from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["parser_fixture", "live_snapshot"])
def extraction(request):
    if request.param == "parser_fixture":
        path = ROOT / "evals/check-runs/20260926-pdf-parser-selection/adapter-2/apple-fy24.json"
        return PdfExtraction.model_validate_json(path.read_text())
    snapshot = json.loads((ROOT / "evals/library-runs/20260927-v2-pdf-live/index-snapshot.json").read_text())
    apple = next(item for item in snapshot["files"] if item["file"]["file_name"] == "apple-fy24.pdf")
    return PdfExtraction.model_validate(apple["extraction"])


def sales_row(extraction):
    table = next(block.table for block in extraction.blocks if block.table)
    label = next(cell for cell in table.cells if cell.text == "Total net sales (1)")
    cells = [cell for cell in table.cells if cell.row_start == label.row_start]
    return min(cell.start_offset for cell in cells), max(cell.end_offset for cell in cells)


def test_split_sales_row_retains_exact_units_and_period_context(extraction):
    start, end = sales_row(extraction)
    evidence = pdf_evidence(extraction, start, end)

    assert "94,930" in extraction.text[start:end]
    assert "391,035" in extraction.text[start:end]
    assert "In millions" not in extraction.text[start:end]
    assert any("Three Months Ended" in extra.text for extra in evidence.supplements)
    assert any("Twelve Months Ended" in extra.text for extra in evidence.supplements)
    preceding = [extra for extra in evidence.supplements if extra.role == "preceding_text"]
    assert len(preceding) == 1
    source = extraction.blocks[2]
    assert preceding[0].text == source.text
    assert preceding[0].text.startswith("(In millions,")
    assert preceding[0].regions == list(source.regions)
    assert {region.page_index for region in preceding[0].regions} == {0}
    assert preceding[0].table_id == extraction.blocks[3].table.table_id
    assert all(extra.text == extraction.text[extra.start_offset:extra.end_offset]
               for extra in evidence.supplements)


def test_units_already_in_excerpt_are_not_repeated(extraction):
    start = extraction.blocks[2].start_offset
    _, end = sales_row(extraction)

    evidence = pdf_evidence(extraction, start, end)

    assert "In millions" in extraction.text[start:end]
    assert not any(extra.role == "preceding_text" for extra in evidence.supplements)


@pytest.mark.parametrize("reference", ["caption_refs", "note_refs"])
def test_parser_associated_units_are_not_added_twice(extraction, reference):
    blocks = list(extraction.blocks)
    table = blocks[3].table.model_copy(update={reference: (blocks[2].source_ref,)})
    blocks[3] = blocks[3].model_copy(update={"table": table})
    extraction = extraction.model_copy(update={"blocks": tuple(blocks)})

    evidence = pdf_evidence(extraction, *sales_row(extraction))

    units = [extra for extra in evidence.supplements if extra.start_offset == blocks[2].start_offset]
    assert len(units) == 1
    assert units[0].role == ("caption" if reference == "caption_refs" else "note")


@pytest.mark.parametrize("boundary", ["heading", "page", "block_kind"])
def test_preceding_context_stays_within_its_table_section(extraction, boundary):
    blocks = list(extraction.blocks)
    previous = blocks[2]
    if boundary == "heading":
        previous = previous.model_copy(update={"heading_path": ("Other section",)})
    elif boundary == "page":
        regions = tuple(region.model_copy(update={"page_index": 1}) for region in previous.regions)
        previous = previous.model_copy(update={"regions": regions})
    else:
        previous = previous.model_copy(update={"kind": "heading"})
    blocks[2] = previous
    extraction = extraction.model_copy(update={"blocks": tuple(blocks)})

    evidence = pdf_evidence(extraction, *sales_row(extraction))

    assert not any(extra.role == "preceding_text" for extra in evidence.supplements)


def test_doclaynet_running_headers_are_not_table_context():
    snapshot = json.loads((ROOT / "evals/library-runs/20260927-v2-pdf-live/index-snapshot.json").read_text())
    paper = next(item for item in snapshot["files"] if item["file"]["file_name"] == "doclaynet.pdf")
    extraction = PdfExtraction.model_validate(paper["extraction"])
    table_refs = {"#/tables/0", "#/tables/1", "#/tables/2", "#/tables/4"}

    for index, table in enumerate(extraction.blocks):
        if table.source_ref not in table_refs:
            continue
        header = extraction.blocks[index - 1]
        assert header.kind == "paragraph" and header.label == "page_header"
        assert "KDD" in header.text

        evidence = pdf_evidence(extraction, table.start_offset, table.end_offset)

        assert not any(extra.role == "preceding_text" for extra in evidence.supplements)
        assert not any(extra.start_offset == header.start_offset for extra in evidence.supplements)


def test_continued_currency_table_retains_previous_page_periods_and_units():
    snapshot = json.loads((ROOT / "evals/library-runs/20261001-new-pdf-acceptance/index-snapshot.json").read_text())
    doc = next(item for item in snapshot["files"] if item["file"]["file_name"] == "nvidia-fy25.pdf")
    extraction = PdfExtraction.model_validate(doc["extraction"])
    block = next(b for b in extraction.blocks if b.source_ref == "#/tables/9")
    evidence = pdf_evidence(extraction, block.start_offset, block.end_offset)

    assert any("Three Months Ended" in s.text for s in evidence.supplements)
    assert any("Twelve Months Ended" in s.text for s in evidence.supplements)
    assert any("In millions, except per share data" in s.text for s in evidence.supplements)
    assert all(s.text == extraction.text[s.start_offset:s.end_offset] for s in evidence.supplements)
    assert {r.page_index for s in evidence.supplements for r in s.regions} == {6}
    reading = evidence.tables[0].reading
    assert '["Three Months Ended > January 26, 2025","$ 24,034"]' in reading
    assert '["Twelve Months Ended > January 26, 2025","$ 81,453"]' in reading
    assert '["$ 3,378","$ 24,034"]' not in reading
    # The observed false header is also a body value, not discarded evidence.
    assert '["Three Months Ended > January 26, 2025","$ 3,378"]' in reading
    assert next(c for c in block.table.cells if c.text == "$ 3,378").column_header


def test_continuation_context_does_not_cross_a_new_section():
    snapshot = json.loads((ROOT / "evals/library-runs/20261001-new-pdf-acceptance/index-snapshot.json").read_text())
    doc = next(item for item in snapshot["files"] if item["file"]["file_name"] == "nvidia-fy25.pdf")
    extraction = PdfExtraction.model_validate(doc["extraction"])
    blocks = list(extraction.blocks)
    i = next(i for i, b in enumerate(blocks) if b.source_ref == "#/tables/9")
    blocks[i] = blocks[i].model_copy(update={"heading_path": ("Different financial statement",)})
    extraction = extraction.model_copy(update={"blocks": tuple(blocks)})
    evidence = pdf_evidence(extraction, blocks[i].start_offset, blocks[i].end_offset)
    assert not any(r.page_index == 6 for s in evidence.supplements for r in s.regions)
