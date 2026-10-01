"""Search ready chunks, expand children, and pack exact evidence within a budget."""

from time import perf_counter

from sqlalchemy.orm import Session

from knowledgebase.config import (
    DEFAULT_TOP_K, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER, RetrievalOptions,
    DEFAULT_EVIDENCE_PACKING_STRATEGY,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.bm25 import search_bm25
from knowledgebase.rag.fusion import fuse_rrf
from knowledgebase.rag.reranking import rerank
from knowledgebase.rag.scope import document_references, identity_labels, resolve_document_scope, prioritize_documents
from knowledgebase.schemas import (
    ChildChunk, RetrievedChunk, RetrievedEvidence, DocumentScope, FileInfo,
    RetrievalCandidate, RetrievalDiagnostics, RerankCandidate, StructuredChunk, ScopeFile,
)
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.operations import (
    get_chunks_by_ids, get_chunks_for_files, get_files, get_parents_by_ids, get_source_texts, get_pdf_extraction,
)


def retrieve_evidence(
    question: str, session: Session, embedding_client: EmbeddingClient,
    vector_store: ChromaStore, top_k: int = DEFAULT_TOP_K,
    *, evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    scope_question: str | None = None,
) -> RetrievedEvidence:
    """Retrieve candidates, then expand and pack one final evidence context."""
    candidates = retrieve_candidates(
        question, session, embedding_client, vector_store, top_k,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client,
        file_ids=file_ids, scope_question=scope_question,
    )
    if candidates.diagnostics.embedding_seconds is None:
        return RetrievedEvidence(chunks=[], diagnostics=candidates.diagnostics)
    return pack_retrieval_candidates(candidates.chunks, session, candidates.diagnostics)


def retrieve_candidates(
    question: str, session: Session, embedding_client: EmbeddingClient,
    vector_store: ChromaStore, top_k: int = DEFAULT_TOP_K,
    *, evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    scope_question: str | None = None,
    allowed_file_ids: list[str] | None = None,
    prioritize_scope: bool = True,
) -> RetrievedEvidence:
    """Search ready children before expansion or packing; retain query-local ranks."""
    if top_k <= 0:
        raise ValueError("top_k must be positive.")
    if evidence_max_tokens <= 0:
        raise ValueError("evidence_max_tokens must be positive.")
    options = retrieval_options or RetrievalOptions()
    options = options.model_copy(update={
        "packing_strategy": options.packing_strategy or DEFAULT_EVIDENCE_PACKING_STRATEGY,
    })
    if options.rerank_enabled and reranker_client is None:
        raise ValueError("Enabled reranking requires a reranker client.")
    diagnostics = RetrievalDiagnostics(
        max_tokens=evidence_max_tokens, tokenizer=encoding_name, options=options, top_k=top_k,
    )
    started = perf_counter()
    ready_files, scope = resolve_ready_scope(
        question, session, file_ids=file_ids, scope_question=scope_question,
        allowed_file_ids=allowed_file_ids,
    )
    diagnostics.document_scope = scope
    if scope is not None:
        diagnostics.scope_seconds = perf_counter() - started
    if not ready_files:
        return RetrievedEvidence(chunks=[], diagnostics=diagnostics)

    scoped_files = diagnostics.document_scope.matches if diagnostics.document_scope else []
    labels_by_file = {file.file_id: file.labels for file in scoped_files}
    multiple_documents = len(scoped_files) > 1
    balance_documents = multiple_documents and prioritize_scope
    embedding_started = perf_counter()
    query_embedding = embedding_client.embed_query(question)
    diagnostics.embedding_seconds = perf_counter() - embedding_started
    search_limit = options.candidate_limit if options.strategy == "hybrid" else top_k
    groups = [[identity] for identity in ready_files] if multiple_documents else [list(ready_files)]
    matches = [match for group in groups for match in vector_store.search(
        query_embedding, top_k=search_limit, file_ids=group,
    )]
    diagnostics.vector_matches = sorted(matches, key=lambda m: (m.distance, m.chunk_id))
    fusion_by_id = {}
    rerank_by_id = {}
    if options.strategy == "hybrid":
        corpus = get_chunks_for_files(session, list(ready_files))
        diagnostics.bm25_matches = search_bm25(
            question, corpus, top_k=options.candidate_limit, k1=options.bm25_k1, b=options.bm25_b,
        )
        diagnostics.fused_matches = fuse_rrf(
            diagnostics.bm25_matches, diagnostics.vector_matches,
            limit=max(1, len(diagnostics.bm25_matches) + len(matches)), k=options.rrf_k,
        )
        fusion_by_id = {match.chunk_id: match for match in diagnostics.fused_matches}
        files_by_chunk = {chunk.chunk_id: chunk.file_id for chunk in corpus}
        if options.rerank_enabled:
            corpus_by_id = {chunk.chunk_id: chunk for chunk in corpus}
            scoring_parents = {}
            if options.rerank_unit == "parent":
                scoring_parents = {parent.parent_id: parent for parent in get_parents_by_ids(
                    session, [corpus_by_id[match.chunk_id].parent_id
                              for match in diagnostics.fused_matches
                              if isinstance(corpus_by_id[match.chunk_id], ChildChunk)],
                )}
            candidates, seen = [], set()
            window = diagnostics.fused_matches
            if balance_documents:
                window = [fusion_by_id[identity] for identity in prioritize_documents(
                    [match.chunk_id for match in window], files_by_chunk, len(window),
                )]
            for match in window:
                child = corpus_by_id[match.chunk_id]
                parent = (scoring_parents.get(child.parent_id) if isinstance(child, ChildChunk) else None)
                identity = parent.parent_id if parent else child.chunk_id
                if identity in seen:
                    continue
                seen.add(identity)
                region = parent or child
                candidates.append(RerankCandidate(
                    **match.model_dump(), text=region.text,
                    heading_path=getattr(region, "heading_path", []),
                    scoring_parent_id=parent.parent_id if parent else None,
                ))
                if len(candidates) == options.rerank_candidate_limit:
                    break
            started = perf_counter()
            diagnostics.rerank = rerank(
                question, candidates, reranker_client, top_k=top_k,
                candidate_limit=options.rerank_candidate_limit,
                max_input_tokens=options.rerank_max_input_tokens, encoding_name=encoding_name,
            )
            diagnostics.rerank_seconds = perf_counter() - started
            selected = diagnostics.rerank.matches if balance_documents else diagnostics.rerank.selected
            rerank_by_id = {match.chunk_id: match for match in selected}
        else:
            selected = diagnostics.fused_matches if balance_documents else diagnostics.fused_matches[:top_k]
        selected_ids = [match.chunk_id for match in selected]
        if balance_documents:
            selected_ids = prioritize_documents(selected_ids, files_by_chunk, top_k)
        chunks = [corpus_chunk for corpus_chunk in corpus if corpus_chunk.chunk_id in selected_ids]
    else:
        selected_ids = [match.chunk_id for match in diagnostics.vector_matches]
        if not balance_documents:
            selected_ids = selected_ids[:top_k]
        chunks = get_chunks_by_ids(session, selected_ids)
        if balance_documents:
            selected_ids = prioritize_documents(selected_ids, {chunk.chunk_id: chunk.file_id for chunk in chunks}, top_k)
    distances = {match.chunk_id: match.distance for match in matches}
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    child_hits: list[RetrievedChunk] = []
    for chunk_id in selected_ids:
        chunk = chunks_by_id[chunk_id]
        provenance = {"distance": distances.get(chunk_id), "fusion": fusion_by_id.get(chunk_id),
                      "rerank": rerank_by_id.get(chunk_id)}
        identity_labels_for_chunk = labels_by_file.get(chunk.file_id, [])
        parent_id = chunk.parent_id if isinstance(chunk, ChildChunk) else None
        diagnostics.candidates.append(RetrievalCandidate(
            chunk_id=chunk_id, **provenance, file_id=chunk.file_id, parent_id=parent_id,
            text=chunk.text, start_offset=chunk.start_offset, end_offset=chunk.end_offset,
        ))
        child_hits.append(RetrievedChunk(
            chunk=chunk, file_name=ready_files[chunk.file_id].file_name, **provenance,
            document_labels=identity_labels_for_chunk,
            parent_id=parent_id, matched_child_ids=[chunk_id] if parent_id else [],
        ))
    return RetrievedEvidence(chunks=child_hits, diagnostics=diagnostics)


def resolve_ready_scope(
    question: str, session: Session, *, file_ids: list[str] | None = None,
    scope_question: str | None = None, allowed_file_ids: list[str] | None = None,
) -> tuple[dict[str, FileInfo], DocumentScope | None]:
    """Resolve a document request inside the caller's ready-file boundary."""
    ready_files = {file.file_id: file for file in get_files(session)
                   if file.status == "ready" and (allowed_file_ids is None or file.file_id in allowed_file_ids)}
    references = document_references(scope_question or question)
    if not references and scope_question:
        references = document_references(question)
    scope = None
    if references or file_ids is not None:
        texts = get_source_texts(session, list(ready_files)) if references else {}
        scope = resolve_document_scope(references, [ScopeFile(
            file_id=file.file_id, file_name=file.file_name,
            labels=identity_labels(file.file_name, texts.get(file.file_id, "")),
        ) for file in ready_files.values()], file_ids=file_ids)
        ready_files = {identity: file for identity, file in ready_files.items() if identity in scope.file_ids}
    return ready_files, scope


def pack_retrieval_candidates(
    child_hits: list[RetrievedChunk], session: Session, diagnostics: RetrievalDiagnostics,
) -> RetrievedEvidence:
    """Expand a selected, deduplicated child list and charge one context budget."""
    parents = {parent.parent_id: parent for parent in get_parents_by_ids(
        session, [hit.parent_id for hit in child_hits if hit.parent_id is not None],
    )}
    regions: dict[str, RetrievedChunk] = {}
    for hit in child_hits:
        chunk, parent_id = hit.chunk, hit.parent_id
        if parent_id is not None:
            if parent_id in regions:
                regions[parent_id].matched_child_ids.append(chunk.chunk_id)
                continue
            parent = parents[parent_id]
            excerpt = StructuredChunk(chunk_id=parent.parent_id, **parent.model_dump(exclude={"parent_id"}))
            regions[parent_id] = hit.model_copy(update={"chunk": excerpt, "matched_child_ids": [chunk.chunk_id]})
        else:
            regions[chunk.chunk_id] = hit.model_copy()
    pdfs = {identity: get_pdf_extraction(session, identity) for identity in {hit.chunk.file_id for hit in child_hits}}
    for region in [*child_hits, *regions.values()]:
        pdf = pdfs[region.chunk.file_id]
        if pdf is not None:
            region.pdf = pdf_evidence(pdf, region.chunk.start_offset, region.chunk.end_offset)
    return pack_evidence(child_hits, list(regions.values()), diagnostics)
