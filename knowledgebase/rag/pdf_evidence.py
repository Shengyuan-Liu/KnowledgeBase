"""Locate PDF evidence and retain separately cited table context before packing."""

import json

from knowledgebase.rag.pdf_models import PdfBlock, PdfExtraction, PdfTable
from knowledgebase.schemas import PdfEvidence, PdfSupplement, PdfTableSpan


def table_rows(extraction: PdfExtraction) -> dict[int, list[tuple[int, int]]]:
    result = {}
    for index, block in enumerate(extraction.blocks):
        if block.table is None:
            continue
        rows: dict[int, list] = {}
        for cell in block.table.cells:
            rows.setdefault(cell.row_start, []).append(cell)
        result[index] = [(min(c.start_offset for c in cells), max(c.end_offset for c in cells))
                         for _, cells in sorted(rows.items())]
    return result


def _preceding_table_text(extraction: PdfExtraction, index: int) -> PdfBlock | None:
    """Keep an adjacent paragraph as context without inferring what it means."""
    if index == 0:
        return None
    previous, table = extraction.blocks[index - 1:index + 1]
    pages = {r.page_index for r in table.regions}
    if (previous.kind == "paragraph" and previous.label not in {"page_header", "page_footer"}
            and previous.heading_path == table.heading_path
            and pages and {r.page_index for r in previous.regions} == {min(pages)}):
        return previous
    return None


def _table_reading(table: PdfTable, start: int, end: int) -> str:
    """Bind complete supplied cells to their row labels and parent/leaf headers."""
    headers = sorted((c for c in table.cells if c.column_header and c.text.strip()
                      and (table.columns == 1 or c.column_end - c.column_start < table.columns)),
                     key=lambda c: (c.row_start, c.column_start))
    rows = {}
    for cell in table.cells:
        if (not cell.column_header and start <= cell.start_offset and cell.end_offset <= end
                and cell.start_offset < end and start < cell.end_offset):
            rows.setdefault((cell.row_start, cell.row_end), []).append(cell)
    lines = []
    for (row_start, row_end), cells in sorted(rows.items()):
        labels = [c for c in table.cells if c.row_header
                  and c.row_start < row_end and row_start < c.row_end]
        values = []
        for cell in sorted(cells, key=lambda c: c.column_start):
            if cell.row_header:
                continue
            path = [" ".join(h.text.split()) for h in headers
                    if h.column_start <= cell.column_start and cell.column_end <= h.column_end]
            column = " > ".join(path) or f"Column {cell.column_start}:{cell.column_end}"
            values.append([column, cell.text if cell.text else {"state": "blank"}])
        label = " / ".join(c.text for c in labels)
        bounds = f"{min(c.start_offset for c in cells)}:{max(c.end_offset for c in cells)}"
        lines.append(f"Row {row_start}:{row_end} {json.dumps(label, ensure_ascii=False)} "
                     f"(canonical offsets {bounds}): "
                     + json.dumps(values, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(lines)


def pdf_evidence(extraction: PdfExtraction, start: int, end: int) -> PdfEvidence:
    supplements = []
    tables = []
    by_ref = {b.source_ref: b for b in extraction.blocks}
    for index, block in enumerate(extraction.blocks):
        if block.table is None or block.end_offset <= start or end <= block.start_offset:
            continue
        table = block.table
        selected = [c for c in table.cells if c.start_offset < end and start < c.end_offset]
        # Include coordinates for supplied body cells and any separately supplied headers.
        context_cells = [c for c in table.cells if c.column_header or (
            c.row_header and any(c.row_start < hit.row_end and hit.row_start < c.row_end for hit in selected)
        )]
        cells = list(selected)
        for cell in context_cells:
            if cell not in cells:
                cells.append(cell)
            if cell.text and not (start <= cell.start_offset and cell.end_offset <= end):
                supplements.append(PdfSupplement(
                    role="column_header" if cell.column_header else "row_header",
                    table_id=table.table_id, text=cell.text,
                    start_offset=cell.start_offset, end_offset=cell.end_offset,
                    regions=list(cell.regions or extraction.locate(cell.start_offset, cell.end_offset)),
                ))
        for role, refs in [("caption", table.caption_refs), ("note", table.note_refs)]:
            for ref in refs:
                associated = by_ref.get(ref)
                if associated is not None and not (start <= associated.start_offset and associated.end_offset <= end):
                    supplements.append(PdfSupplement(
                        role=role, table_id=table.table_id, text=associated.text,
                        start_offset=associated.start_offset, end_offset=associated.end_offset,
                        regions=list(associated.regions),
                    ))
        previous = _preceding_table_text(extraction, index)
        if (previous is not None
                and previous.source_ref not in (*table.caption_refs, *table.note_refs)
                and not (start <= previous.start_offset and previous.end_offset <= end)):
            supplements.append(PdfSupplement(
                role="preceding_text", table_id=table.table_id, text=previous.text,
                start_offset=previous.start_offset, end_offset=previous.end_offset,
                regions=list(previous.regions),
            ))
        tables.append(PdfTableSpan(table_id=table.table_id, cells=[
            (c.row_start, c.row_end, c.column_start, c.column_end, c.start_offset, c.end_offset)
            for c in cells
        ], column_header_spans=[(c.start_offset, c.end_offset) for c in table.cells if c.column_header],
            reading=_table_reading(table, start, end)))
    regions = list(extraction.locate(start, end))
    pages = {r.page_index for r in regions}
    pages.update(r.page_index for s in supplements for r in s.regions)
    warnings = [w for w in extraction.warnings if not w.page_indices or pages.intersection(w.page_indices)]
    return PdfEvidence(
        revision_id=extraction.revision_id, source_hash=extraction.source_hash,
        page_count=extraction.page_count, regions=regions, tables=tables,
        supplements=supplements, warnings=warnings,
    )
