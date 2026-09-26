"""Locate PDF evidence and retain separately cited table context before packing."""

from knowledgebase.rag.pdf_models import PdfExtraction
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


def pdf_evidence(extraction: PdfExtraction, start: int, end: int) -> PdfEvidence:
    supplements = []
    tables = []
    by_ref = {b.source_ref: b for b in extraction.blocks}
    for block in extraction.blocks:
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
        tables.append(PdfTableSpan(table_id=table.table_id, cells=[
            (c.row_start, c.row_end, c.column_start, c.column_end, c.start_offset, c.end_offset)
            for c in cells
        ]))
    regions = list(extraction.locate(start, end))
    pages = {r.page_index for r in regions}
    pages.update(r.page_index for s in supplements for r in s.regions)
    warnings = [w for w in extraction.warnings if not w.page_indices or pages.intersection(w.page_indices)]
    return PdfEvidence(
        revision_id=extraction.revision_id, source_hash=extraction.source_hash,
        page_count=extraction.page_count, regions=regions, tables=tables,
        supplements=supplements, warnings=warnings,
    )
