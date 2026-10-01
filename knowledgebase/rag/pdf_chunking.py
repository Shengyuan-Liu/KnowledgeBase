"""Keep an isolated PDF heading with the following body in its parent context."""

import tiktoken

from knowledgebase.schemas import (
    PdfExtraction, ParentChildChunks,
)


PDF_PARENT_CONTEXT_VERSION = "adjacent-heading-body-v1"


def join_heading_parents(extraction: PdfExtraction, chunks: ParentChildChunks) -> ParentChildChunks:
    """Join adjacent heading-only/body parents on one page when their budget fits.

    Docling can emit a slide title and its learning-phase heading at the same
    level. Keep that title with the next body without guessing a heading level.
    Children retain their exact text, IDs, offsets and heading paths; only their
    parent links change. Existing extraction records are not modified.
    """
    parents = []
    parent_ids = {}
    for parent in chunks.parents:
        parent_ids[parent.parent_id] = parent.parent_id
        if parents:
            previous = parents[-1]
            heading_only = all(extraction.blocks[i].kind == "heading" for i in previous.source_block_indices)
            has_body = any(extraction.blocks[i].kind != "heading"
                           and extraction.blocks[i].label not in {"page_header", "page_footer"}
                           for i in parent.source_block_indices)
            if heading_only and has_body:
                previous_pages = {r.page_index for r in extraction.locate(previous.start_offset, previous.end_offset)}
                current_pages = {r.page_index for r in extraction.locate(parent.start_offset, parent.end_offset)}
                if len(previous_pages) != 1 or current_pages != previous_pages:
                    parents.append(parent)
                    continue
                text = extraction.text[previous.start_offset:parent.end_offset]
                tokens = len(tiktoken.get_encoding(previous.tokenizer).encode_ordinary(text))
                if tokens <= previous.max_tokens:
                    parents[-1] = previous.model_copy(update={
                        "text": text, "end_offset": parent.end_offset, "token_count": tokens,
                        "source_block_indices": list(dict.fromkeys([
                            *previous.source_block_indices, *parent.source_block_indices,
                        ])),
                    })
                    parent_ids[parent.parent_id] = previous.parent_id
                    continue
        parents.append(parent)
    renamed = {parent.parent_id: f"{parent.file_id}:parent:{i}" for i, parent in enumerate(parents)}
    return ParentChildChunks(
        parents=[parent.model_copy(update={"parent_id": renamed[parent.parent_id], "index": i})
                 for i, parent in enumerate(parents)],
        children=[child.model_copy(update={"parent_id": renamed[parent_ids[child.parent_id]]})
                  for child in chunks.children],
    )
