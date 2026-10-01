"""Pack parent context or complete child hits in selected relevance order."""

from time import perf_counter

import tiktoken

from knowledgebase.rag.context import CONTEXT_FORMAT, LABELED_CONTEXT_FORMAT, PDF_CONTEXT_FORMAT, build_context
from knowledgebase.schemas import ExcludedEvidence, RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics


def pack_evidence(
    selected: list[RetrievedChunk], expanded: list[RetrievedChunk], diagnostics: RetrievalDiagnostics,
) -> RetrievedEvidence:
    """Try each parent and its child fallback before lower-ranked evidence.

    Expanded regions are deduplicated and follow their best selected child's rank.
    A rejected parent is tried only once; its selected children may fit separately.
    Every trial counts the actual numbered context in selected-hit order. Parent
    and child text never coexist for the same parent. Parent-first alone remains
    available as the control.
    """
    started = perf_counter()
    diagnostics.context_format = (PDF_CONTEXT_FORMAT if any(c.pdf for c in selected) else
                                  LABELED_CONTEXT_FORMAT if any(c.document_labels for c in selected) else CONTEXT_FORMAT)
    encoding = tiktoken.get_encoding(diagnostics.tokenizer)

    def tokens(regions):
        return len(encoding.encode_ordinary(build_context(regions)))

    def omitted(region):
        return ExcludedEvidence(
            chunk_id=region.chunk.chunk_id, file_id=region.chunk.file_id,
            token_count=len(encoding.encode_ordinary(region.chunk.text)),
        )

    packed: list[RetrievedChunk] = []
    parent_first = diagnostics.options.packing_strategy == "parent_first"
    admitted: set[str] = set()
    if parent_first:
        for region in expanded:
            if tokens([*packed, region]) <= diagnostics.max_tokens:
                packed.append(region)
                admitted.add(region.chunk.chunk_id)
    else:
        by_id = {region.chunk.chunk_id: region for region in expanded}
        attempted: set[str] = set()
        for child in selected:
            identity = child.parent_id or child.chunk.chunk_id
            if identity in admitted:
                continue
            if identity not in attempted:
                attempted.add(identity)
                region = by_id[identity]
                if tokens([*packed, region]) <= diagnostics.max_tokens:
                    packed.append(region)
                    admitted.add(identity)
                    continue
            if child.parent_id is not None and tokens([*packed, child]) <= diagnostics.max_tokens:
                packed.append(child)

    represented = {region.chunk.chunk_id for region in packed}
    represented.update(child_id for region in packed for child_id in region.matched_child_ids)
    diagnostics.excluded = [omitted(region) for region in (expanded if parent_first else selected)
                            if region.chunk.chunk_id not in represented]
    diagnostics.unexpanded_parents = [omitted(region) for region in expanded
                                     if region.parent_id is not None and region.chunk.chunk_id not in admitted
                                     and any(identity in represented for identity in region.matched_child_ids)]
    diagnostics.evidence_tokens = tokens(packed)
    diagnostics.packing_seconds = perf_counter() - started
    return RetrievedEvidence(chunks=packed, diagnostics=diagnostics)
