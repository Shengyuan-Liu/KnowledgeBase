"""Keep admitted parent context and fill unused space with complete selected hits."""

from time import perf_counter

import tiktoken

from knowledgebase.rag.context import CONTEXT_FORMAT, LABELED_CONTEXT_FORMAT, PDF_CONTEXT_FORMAT, build_context
from knowledgebase.schemas import ExcludedEvidence, RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics


def pack_evidence(
    selected: list[RetrievedChunk], expanded: list[RetrievedChunk], diagnostics: RetrievalDiagnostics,
) -> RetrievedEvidence:
    """Pack whole parents, then retain selected children of parents that did not fit.

    Expanded regions are deduplicated and follow their best selected child's rank.
    The second pass never evicts an admitted parent. Every trial counts the actual
    numbered context in selected-hit order; parent and child text never coexist
    for the same parent. Parent-first alone remains available as the control.
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
    for region in expanded:
        if tokens([*packed, region]) <= diagnostics.max_tokens:
            packed.append(region)
    admitted = {region.chunk.chunk_id for region in packed}
    parents = {region.parent_id: region for region in packed if region.parent_id is not None}
    retained = {region.chunk.chunk_id for region in packed if region.parent_id is None}
    parent_first = diagnostics.options.packing_strategy == "parent_first"
    if not parent_first:
        def plan(child_ids):
            regions, seen = [], set()
            for child in selected:
                if child.parent_id in parents:
                    if child.parent_id not in seen:
                        regions.append(parents[child.parent_id])
                        seen.add(child.parent_id)
                elif child.chunk.chunk_id in child_ids:
                    regions.append(child)
            return regions

        for child in selected:
            if child.parent_id in parents or child.chunk.chunk_id in retained:
                continue
            trial = plan(retained | {child.chunk.chunk_id})
            if tokens(trial) <= diagnostics.max_tokens:
                retained.add(child.chunk.chunk_id)
                packed = trial

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
