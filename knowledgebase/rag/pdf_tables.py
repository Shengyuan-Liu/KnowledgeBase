"""Recover collapsed numeric tables from native PDF rules and text rows."""

from dataclasses import asdict
from io import BytesIO

from docling_core.types.doc import BoundingBox, DoclingDocument, TableCell, TableData
import pdfplumber
from pdfplumber.table import Table, TableSettings


ROW_SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "text"}
RECOVERY_SETTINGS = {
    "algorithm": "collapsed-ruled-numeric-table-v1",
    "eligibility": "single-page Docling table with at most one row or column",
    "row_detection": asdict(TableSettings.resolve(ROW_SETTINGS)),
    "grid": "native vertical rules with text-row boundaries extended across the crop",
    "headers": "rows before the first labeled row with at least two numeric cells and a numeric majority",
}


def _numeric(text: str | None) -> bool:
    return bool(text) and text.replace(",", "").isdigit()


def _table_data(table: Table) -> TableData | None:
    """Keep native merged cells and blanks; infer headers only for numeric bodies."""
    rows = table.extract()
    body_start = next((i for i, row in enumerate(rows)
                       if row[0] and not _numeric(row[0])
                       and sum(_numeric(value) for value in row) >= 2
                       and sum(_numeric(value) for value in row) > sum(bool(value) for value in row) / 2), None)
    if body_start is None:
        return None
    xs = sorted({x for cell in table.cells for x in (cell[0], cell[2])})
    ys = sorted({y for cell in table.cells for y in (cell[1], cell[3])})
    header_end = table.rows[body_start].bbox[1]
    cells = []
    for row, texts in zip(table.rows, rows):
        for bbox, text in zip(row.cells, texts):
            if bbox is None:  # Covered by a merged cell, not a blank value.
                continue
            left, top, right, bottom = bbox
            r0, r1 = ys.index(top), ys.index(bottom)
            c0, c1 = xs.index(left), xs.index(right)
            cells.append(TableCell(
                text=text, bbox=BoundingBox(l=left, t=top, r=right, b=bottom, coord_origin="TOPLEFT"),
                start_row_offset_idx=r0, end_row_offset_idx=r1, row_span=r1 - r0,
                start_col_offset_idx=c0, end_col_offset_idx=c1, col_span=c1 - c0,
                column_header=top < header_end, row_header=top >= header_end and c0 == 0,
            ))
    return TableData(num_rows=len(ys) - 1, num_cols=len(xs) - 1, table_cells=cells)


def recover_collapsed_tables(document: DoclingDocument, source: bytes) -> tuple[str, ...]:
    """Replace only collapsed single-page tables with a native ruled numeric grid.

    Docling remains responsible for layout and all other tables. Text-row edges
    normally end at the outermost words, which can omit the row-label column;
    extending those edges across the detected table includes its native border.
    This uses digital text and drawn rules, never OCR or inferred missing values.
    """
    collapsed = [item for item in document.tables if len(item.prov) == 1
                 and (item.data.num_rows <= 1 or item.data.num_cols <= 1)]
    if not collapsed:
        return ()
    recovered = []
    with pdfplumber.open(BytesIO(source)) as pdf:
        for item in collapsed:
            provenance = item.prov[0]
            page = pdf.pages[provenance.page_no - 1]
            box = provenance.bbox.to_top_left_origin(page.height)
            crop = page.crop((box.l, box.t, box.r, box.b))
            edges = crop.debug_tablefinder(ROW_SETTINGS).edges
            boundaries = sorted({edge["top"] for edge in edges if edge["orientation"] == "h"})
            if len(boundaries) < 2:
                continue  # No native text rows to reconstruct.
            tables = crop.find_tables({
                "vertical_strategy": "lines", "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": boundaries,
            })
            if len(tables) != 1:
                continue  # A partial grid does not replace the detected table.
            data = _table_data(tables[0])
            if data is not None:
                item.data = data
                recovered.append(item.self_ref)
    return tuple(recovered)
