"""Build budgeted source context with explicit identity and unchanged excerpts."""

import json
from collections.abc import Callable

from knowledgebase.schemas import RetrievedChunk


PDF_CONTEXT_FORMAT = "source-metadata-pdf-v4"
CONTEXT_FORMAT = "source-metadata-v1"
LABELED_CONTEXT_FORMAT = "source-metadata-v2"


def build_context(chunks: list[RetrievedChunk], *,
                  render_text: Callable[[str, int, str], str] | None = None,
                  render_table_reading: Callable[[str, str], str] | None = None) -> str:
    """Count identity labels as context while preserving canonical source slices."""
    sources = []
    for number, item in enumerate(chunks, start=1):
        identity = {
            "file_name": item.file_name,
            "heading_path": item.chunk.heading_path,
        }
        if item.document_labels:
            identity["document_labels"] = item.document_labels
        metadata = json.dumps(identity, ensure_ascii=False)
        text = (render_text(item.chunk.file_id, item.chunk.start_offset, item.chunk.text)
                if render_text else item.chunk.text)
        context = f"[{number}]\nSource metadata: {metadata}\nExcerpt:\n{text}"
        if item.pdf is not None:
            context += "\nPDF physical pages: " + ", ".join(str(p + 1) for p in sorted({r.page_index for r in item.pdf.regions}))
            context += f"\nExcerpt canonical offsets: {item.chunk.start_offset}:{item.chunk.end_offset}"
            for table in item.pdf.tables:
                if table.reading is not None:
                    reading = (render_table_reading(item.chunk.file_id, table.reading)
                               if render_table_reading else table.reading)
                    context += (f"\nTable readings for {table.table_id} derived from source cells: "
                                'each row lists [full column header, value]. {"state":"blank"} '
                                "means the source cell is blank: report it as blank, not unknown, unavailable, "
                                "or numeric zero. Legacy null markers have the same meaning. "
                                "These markers describe cell contents, not missing excerpts. "
                                "Only complete supplied cells are listed. "
                                "Bounds are exclusive." + ("\n" + reading if reading else ""))
                else:
                    # Saved evidence from earlier versions has coordinates but no reading aid.
                    context += "\nTable cells [row start, row end, column start, column end, canonical start, canonical end]; bounds exclusive; partial cells may intersect excerpt edges: "
                    context += json.dumps([table.model_dump(exclude={"column_header_spans", "reading"})],
                                          ensure_ascii=False, separators=(",", ":"))
            for extra in item.pdf.supplements:
                pages = sorted({r.page_index + 1 for r in extra.regions})
                text = (render_text(item.chunk.file_id, extra.start_offset, extra.text)
                        if render_text else extra.text)
                context += (f"\nSeparately located {extra.role} for {extra.table_id} "
                            f"(pages {pages}, offsets {extra.start_offset}:{extra.end_offset}):\n{text}")
            context += "\nExtraction limitations: " + " ".join(dict.fromkeys(w.message for w in item.pdf.warnings))
        sources.append(context)
    return "\n\n".join(sources)
