"""Search ready chunks, expand children, and pack exact evidence within a budget."""

import tiktoken
from sqlalchemy.orm import Session

from knowledgebase.config import (
    DEFAULT_TOP_K, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER, RetrievalOptions,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.rag.context import build_context
from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.fusion import fuse_rrf
from knowledgebase.schemas import (
    ChildChunk, ExcludedEvidence, RetrievedChunk, RetrievedEvidence,
    RetrievalCandidate, RetrievalDiagnostics, StructuredChunk,
)
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.operations import (
    get_chunks_by_ids, get_chunks_for_files, get_files, get_parents_by_ids,
)


def retrieve(
    question: str,
    session: Session,
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    top_k: int = DEFAULT_TOP_K,
    *, evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
) -> list[RetrievedChunk]:
    """Return packed evidence; use retrieve_evidence for candidates and exclusions."""
    return retrieve_evidence(
        question, session, embedding_client, vector_store, top_k,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options,
    ).chunks


def retrieve_evidence(
    question: str, session: Session, embedding_client: EmbeddingClient,
    vector_store: ChromaStore, top_k: int = DEFAULT_TOP_K,
    *, evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
) -> RetrievedEvidence:
    """Expand selected children, deduplicate parents by best child rank, and pack.

    No ready files means no evidence and no embedding request. The caller owns
    the session. The budget counts the exact numbered context, including labels
    and separators; an oversized region is skipped whole and recorded. Flat
    chunks remain supported, without inventing parents for previously stored data.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive.")
    if evidence_max_tokens <= 0:
        raise ValueError("evidence_max_tokens must be positive.")
    options = retrieval_options or RetrievalOptions()
    diagnostics = RetrievalDiagnostics(
        max_tokens=evidence_max_tokens, tokenizer=encoding_name, options=options, top_k=top_k,
    )
    ready_files = {file.file_id: file for file in get_files(session) if file.status == "ready"}
    if not ready_files:
        return RetrievedEvidence(chunks=[], diagnostics=diagnostics)

    query_embedding = embedding_client.embed_query(question)
    matches = vector_store.search(
        query_embedding,
        top_k=options.candidate_limit if options.strategy == "hybrid" else top_k,
        file_ids=list(ready_files),
    )
    diagnostics.vector_matches = sorted(matches, key=lambda m: (m.distance, m.chunk_id))
    fusion_by_id = {}
    if options.strategy == "hybrid":
        corpus = get_chunks_for_files(session, list(ready_files))
        diagnostics.bm25_matches = search_bm25(
            question, corpus, top_k=options.candidate_limit, k1=options.bm25_k1, b=options.bm25_b,
        )
        diagnostics.fused_matches = fuse_rrf(
            diagnostics.bm25_matches, diagnostics.vector_matches,
            limit=max(1, len(diagnostics.bm25_matches) + len(matches)), k=options.rrf_k,
        )
        selected = diagnostics.fused_matches[:top_k]
        fusion_by_id = {match.chunk_id: match for match in selected}
        selected_ids = list(fusion_by_id)
        chunks = [chunk for chunk in corpus if chunk.chunk_id in fusion_by_id]
    else:
        selected_ids = [match.chunk_id for match in diagnostics.vector_matches[:top_k]]
        chunks = get_chunks_by_ids(session, selected_ids)
    distances = {match.chunk_id: match.distance for match in matches}
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    parents = {parent.parent_id: parent for parent in get_parents_by_ids(
        session, [chunk.parent_id for chunk in chunks if isinstance(chunk, ChildChunk)],
    )}
    regions: dict[str, RetrievedChunk] = {}
    for chunk_id in selected_ids:
        chunk = chunks_by_id[chunk_id]
        provenance = {"distance": distances.get(chunk_id), "fusion": fusion_by_id.get(chunk_id)}
        parent_id = chunk.parent_id if isinstance(chunk, ChildChunk) else None
        diagnostics.candidates.append(RetrievalCandidate(
            chunk_id=chunk_id, **provenance, file_id=chunk.file_id, parent_id=parent_id,
            text=chunk.text, start_offset=chunk.start_offset, end_offset=chunk.end_offset,
        ))
        if parent_id is not None:
            if parent_id in regions:
                regions[parent_id].matched_child_ids.append(chunk.chunk_id)
                continue
            parent = parents[parent_id]
            excerpt = StructuredChunk(chunk_id=parent.parent_id, **parent.model_dump(exclude={"parent_id"}))
            regions[parent_id] = RetrievedChunk(
                chunk=excerpt, file_name=ready_files[chunk.file_id].file_name,
                **provenance, parent_id=parent_id, matched_child_ids=[chunk.chunk_id],
            )
        else:
            regions[chunk.chunk_id] = RetrievedChunk(
                chunk=chunk, file_name=ready_files[chunk.file_id].file_name, **provenance,
            )

    encoding = tiktoken.get_encoding(encoding_name)
    packed: list[RetrievedChunk] = []
    for region in regions.values():
        tokens = len(encoding.encode_ordinary(build_context([*packed, region])))
        if tokens > evidence_max_tokens:
            diagnostics.excluded.append(ExcludedEvidence(
                chunk_id=region.chunk.chunk_id, file_id=region.chunk.file_id,
                token_count=len(encoding.encode_ordinary(region.chunk.text)),
            ))
        else:
            packed.append(region)
            diagnostics.evidence_tokens = tokens
    return RetrievedEvidence(chunks=packed, diagnostics=diagnostics)
