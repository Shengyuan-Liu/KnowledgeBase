"""Reserve exact child evidence before spending remaining context on parents."""

from time import perf_counter

import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.schemas import ExcludedEvidence, RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics


def pack_evidence(
    selected: list[RetrievedChunk], expanded: list[RetrievedChunk], diagnostics: RetrievalDiagnostics,
) -> RetrievedEvidence:
    """Pack whole regions without replacing an admitted child with unrelated context.

    Both lists follow selected-hit order; expanded contains deduplicated parents
    and unchanged flat hits. Parent-first preserves the previous control behavior.
    Child-first admits whole hits by rank, then replaces siblings with their parent
    only if the entire resulting numbered context fits. It never fetches more hits.
    """
    started = perf_counter()
    encoding = tiktoken.get_encoding(diagnostics.tokenizer)

    def tokens(regions):
        return len(encoding.encode_ordinary(build_context(regions)))

    def omitted(region):
        return ExcludedEvidence(
            chunk_id=region.chunk.chunk_id, file_id=region.chunk.file_id,
            token_count=len(encoding.encode_ordinary(region.chunk.text)),
        )

    parent_first = diagnostics.options.packing_strategy == "parent_first"
    initial = expanded if parent_first else selected
    packed: list[RetrievedChunk] = []
    for region in initial:
        if tokens([*packed, region]) <= diagnostics.max_tokens:
            packed.append(region)

    diagnostics.unexpanded_parents = []
    if not parent_first:
        retained = {region.chunk.chunk_id for region in packed}
        parents = {region.parent_id: region for region in expanded if region.parent_id is not None}
        included_parents: set[str] = set()

        def plan(parent_ids):
            regions = []
            seen = set()
            for child in selected:
                if child.parent_id in parent_ids:
                    if child.parent_id not in seen:
                        regions.append(parents[child.parent_id])
                        seen.add(child.parent_id)
                elif child.chunk.chunk_id in retained:
                    regions.append(child)
            return regions

        for parent_id, parent in parents.items():
            if not any(child_id in retained for child_id in parent.matched_child_ids):
                continue
            trial = plan(included_parents | {parent_id})
            if tokens(trial) <= diagnostics.max_tokens:
                included_parents.add(parent_id)
                packed = trial
            else:
                diagnostics.unexpanded_parents.append(omitted(parent))

    represented = {region.chunk.chunk_id for region in packed}
    represented.update(child_id for region in packed for child_id in region.matched_child_ids)
    diagnostics.excluded = [omitted(region) for region in initial if region.chunk.chunk_id not in represented]
    diagnostics.evidence_tokens = tokens(packed)
    diagnostics.packing_seconds = perf_counter() - started
    return RetrievedEvidence(chunks=packed, diagnostics=diagnostics)
