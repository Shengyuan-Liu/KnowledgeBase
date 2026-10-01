"""Search ready chunks, expand children, and pack exact evidence within a budget."""

from copy import copy
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
from knowledgebase.rag.reranking import Reranker
from knowledgebase.rag.scope import document_references, identity_labels, resolve_document_scope, prioritize_documents
from knowledgebase.schemas import (
    RetrievedChunk, RetrievedEvidence, DocumentScope, File, RetrievalCandidate, RetrievalDiagnostics, RerankCandidate, ScopeFile,
)
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.operations import (
    get_chunks_by_ids, get_chunks_for_files, get_files, get_parents_by_ids, get_source_texts, get_pdf_extraction,
)


from knowledgebase.schemas import RetrievalPlan, PlannedQuery, QueryRun, PlanTrace, PlannedEvidence, RequirementEvidence
from collections.abc import Callable
from knowledgebase.rag.planned_retrieval import merge_query_runs, _select_representatives


class Retriever:
    """Reuse search dependencies; callers own each read session and request state."""

    def __init__(self, embeddings: EmbeddingClient, store: ChromaStore, *,
                 top_k: int = DEFAULT_TOP_K, evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
                 encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
                 options: RetrievalOptions | None = None, reranker: Reranker | None = None):
        self.embeddings = embeddings
        self.store = store
        self.top_k = top_k
        self.evidence_max_tokens = evidence_max_tokens
        self.encoding_name = encoding_name
        self.options = options or RetrievalOptions()
        self.reranker = reranker

    def bounded(self, remaining: Callable[[], float]):
        bounded = copy(self)
        bounded.embeddings = self.embeddings.bounded(remaining)
        return bounded

    def retrieve(self, question: str, session: Session, *, file_ids: list[str] | None = None,
                 scope_question: str | None = None) -> RetrievedEvidence:
        """Retrieve candidates and pack one final source-preserving evidence set."""
        candidates = self.retrieve_candidates(question, session, file_ids=file_ids, scope_question=scope_question)
        if candidates.diagnostics.embedding_seconds is None:
            return RetrievedEvidence(chunks=[], diagnostics=candidates.diagnostics)
        return self.pack(candidates.chunks, session, candidates.diagnostics)

    def retrieve_candidates(self, question: str, session: Session, *, top_k: int | None = None,
                            file_ids: list[str] | None = None, scope_question: str | None = None,
                            allowed_file_ids: list[str] | None = None,
                            prioritize_scope: bool = True) -> RetrievedEvidence:
        """Search ready children before expansion or packing; retain query-local ranks."""
        top_k = self.top_k if top_k is None else top_k
        evidence_max_tokens, encoding_name = self.evidence_max_tokens, self.encoding_name
        embedding_client, vector_store = self.embeddings, self.store
        retrieval_options = self.options
        if top_k <= 0:
            raise ValueError("top_k must be positive.")
        if evidence_max_tokens <= 0:
            raise ValueError("evidence_max_tokens must be positive.")
        options = retrieval_options or RetrievalOptions()
        options = options.model_copy(update={
            "packing_strategy": options.packing_strategy or DEFAULT_EVIDENCE_PACKING_STRATEGY,
        })
        if options.rerank_enabled and self.reranker is None:
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
                    scoring_parents = {parent.chunk_id: parent for parent in get_parents_by_ids(
                        session, [corpus_by_id[match.chunk_id].parent_id
                                  for match in diagnostics.fused_matches
                                  if corpus_by_id[match.chunk_id].type == "child"],
                    )}
                candidates, seen = [], set()
                window = diagnostics.fused_matches
                if balance_documents:
                    window = [fusion_by_id[identity] for identity in prioritize_documents(
                        [match.chunk_id for match in window], files_by_chunk, len(window),
                    )]
                for match in window:
                    child = corpus_by_id[match.chunk_id]
                    parent = (scoring_parents.get(child.parent_id) if child.type == "child" else None)
                    identity = parent.chunk_id if parent else child.chunk_id
                    if identity in seen:
                        continue
                    seen.add(identity)
                    region = parent or child
                    candidates.append(RerankCandidate(
                        **match.model_dump(), text=region.text,
                        heading_path=getattr(region, "heading_path", []),
                        scoring_parent_id=parent.chunk_id if parent else None,
                    ))
                    if len(candidates) == options.rerank_candidate_limit:
                        break
                started = perf_counter()
                diagnostics.rerank = self.reranker.rerank(question, candidates, top_k=top_k)
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
            parent_id = chunk.parent_id
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

    @staticmethod
    def pack(child_hits: list[RetrievedChunk], session: Session,
             diagnostics: RetrievalDiagnostics) -> RetrievedEvidence:
        """Expand a selected, deduplicated child list and charge one context budget."""
        parents = {parent.chunk_id: parent for parent in get_parents_by_ids(
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
                excerpt = parent
                regions[parent_id] = hit.model_copy(update={"chunk": excerpt, "matched_child_ids": [chunk.chunk_id]})
            else:
                regions[chunk.chunk_id] = hit.model_copy()
        pdfs = {identity: get_pdf_extraction(session, identity) for identity in {hit.chunk.file_id for hit in child_hits}}
        for region in [*child_hits, *regions.values()]:
            pdf = pdfs[region.chunk.file_id]
            if pdf is not None:
                region.pdf = pdf_evidence(pdf, region.chunk.start_offset, region.chunk.end_offset)
        return pack_evidence(child_hits, list(regions.values()), diagnostics)

    def retrieve_plan(self, plan: RetrievalPlan, session: Session, *,
                      file_ids: list[str] | None = None, allowed_file_ids: list[str] | None = None,
                      checkpoint: Callable[[], object] | None = None,
                      queries: list[PlannedQuery] | None = None,
                      previous_runs: list[QueryRun] | None = None,
                      round_index: int = 1) -> PlannedEvidence:
        """Execute a caller-supplied plan without generation, retries or extra rounds.

        The caller owns the session and retains the returned JSON-serializable trace.
        Provider/schema errors propagate; no partial result is presented as success.
        """
        embedding_client, vector_store = self.embeddings, self.store
        top_k, evidence_max_tokens = self.top_k, self.evidence_max_tokens
        encoding_name, retrieval_options = self.encoding_name, self.options
        started = perf_counter()
        if checkpoint:
            checkpoint()
        if top_k <= 0 or evidence_max_tokens <= 0:
            raise ValueError("top_k and evidence_max_tokens must be positive.")
        options = retrieval_options or RetrievalOptions()
        options = options.model_copy(update={"packing_strategy": options.packing_strategy or DEFAULT_EVIDENCE_PACKING_STRATEGY})
        if options.rerank_enabled and self.reranker is None:
            raise ValueError("Enabled reranking requires a reranker client.")
        ready, scope = resolve_ready_scope(plan.resolved_question, session, file_ids=file_ids,
                                           scope_question=plan.original_question, allowed_file_ids=allowed_file_ids)
        trace = PlanTrace(
            plan=plan, allowed_file_ids=list(ready), document_scope=scope,
            cross_query_rrf_k=options.rrf_k,
            per_query_limit=top_k if plan.route == "direct" else options.candidate_limit,
            top_k=top_k, max_evidence_tokens=evidence_max_tokens,
            scope_seconds=perf_counter() - started,
            stop_reason="scope_unresolved" if scope and scope.status != "resolved" else
                        "no_ready_files" if not ready else "independent_queries_complete",
        )
        diagnostics = RetrievalDiagnostics(max_tokens=evidence_max_tokens, tokenizer=encoding_name,
                                           options=options, top_k=top_k, document_scope=scope)
        # Each round rechecks Ready status. Raw prior results remain in round snapshots.
        for previous in previous_runs or []:
            run = previous.model_copy(deep=True)
            run.result.chunks = [hit for hit in run.result.chunks if hit.chunk.file_id in ready]
            run.result.diagnostics.candidates = [hit for hit in run.result.diagnostics.candidates if hit.file_id in ready]
            trace.runs.append(run)
        batch = plan.queries if queries is None else queries
        # Validate the entire explicit plan scope before making any provider call.
        if ready:
            for query in batch:
                if query.file_ids is not None and not set(query.file_ids) <= ready.keys():
                    raise ValueError(f"Query {query.query_id} attempts to expand the allowed ready-file scope.")
            runs_by_key = {(run.text.strip(), tuple(sorted(set(run.requested_file_ids)))
                           if run.requested_file_ids is not None else None): run for run in trace.runs}
            for query in batch:
                if checkpoint:
                    checkpoint()
                selected_files = query.file_ids if query.file_ids is not None else scope.file_ids if scope else None
                key = (query.text.strip(), tuple(sorted(set(selected_files))) if selected_files is not None else None)
                if key in runs_by_key:
                    run = runs_by_key[key]
                    run.query_ids.append(query.query_id)
                    run.requirement_ids = list(dict.fromkeys([*run.requirement_ids, *query.requirement_ids]))
                    continue
                query_started = perf_counter()
                candidates = self.retrieve_candidates(
                    query.text, session, top_k=trace.per_query_limit,
                    file_ids=selected_files, allowed_file_ids=list(ready),
                    prioritize_scope=plan.route == "direct",
                    scope_question=plan.original_question if plan.route == "direct" else None,
                )
                if checkpoint:
                    checkpoint()
                candidates.diagnostics.retrieval_seconds = perf_counter() - query_started
                run = QueryRun(query_ids=[query.query_id], requirement_ids=list(dict.fromkeys(query.requirement_ids)),
                               round_index=round_index,
                               text=query.text, requested_file_ids=selected_files, result=candidates,
                               seconds=candidates.diagnostics.retrieval_seconds)
                trace.runs.append(run)
                runs_by_key[key] = run
        merge_started = perf_counter()
        if checkpoint:
            checkpoint()
        trace.merged = merge_query_runs(trace.runs, k=options.rrf_k)
        trace.selected_ids = ([hit.chunk.chunk_id for hit in trace.runs[0].result.chunks]
                              if plan.route == "direct" and len(trace.runs) == 1 else
                              _select_representatives(trace.merged, trace.runs, plan, top_k))
        merged_by_id = {candidate.chunk_id: candidate for candidate in trace.merged}
        selected: list[RetrievedChunk] = []
        for identity in trace.selected_ids:
            vote = min(merged_by_id[identity].votes, key=lambda vote: (vote.rank, vote.run_index))
            result = trace.runs[vote.run_index].result
            selected.append(next(hit for hit in result.chunks if hit.chunk.chunk_id == identity).model_copy(deep=True))
            diagnostics.candidates.append(next(candidate for candidate in result.diagnostics.candidates if candidate.chunk_id == identity))
        trace.merge_seconds = perf_counter() - merge_started
        if plan.route == "direct" and len(trace.runs) == 1:
            diagnostics = trace.runs[0].result.diagnostics.model_copy(deep=True)
        evidence = (self.pack(selected, session, diagnostics) if ready else
                    RetrievedEvidence(chunks=[], diagnostics=diagnostics))
        supplied = {hit.chunk.chunk_id for hit in evidence.chunks}
        supplied.update(identity for hit in evidence.chunks for identity in hit.matched_child_ids)
        for requirement in plan.requirements:
            candidates = {hit.chunk.chunk_id for run in trace.runs if requirement.requirement_id in run.requirement_ids
                          for hit in run.result.chunks}
            selected_ids = [identity for identity in trace.selected_ids if identity in candidates]
            trace.requirements.append(RequirementEvidence(
                requirement_id=requirement.requirement_id,
                candidate_ids=[candidate.chunk_id for candidate in trace.merged if candidate.chunk_id in candidates],
                selected_ids=selected_ids, supplied_ids=[identity for identity in selected_ids if identity in supplied],
                budget_excluded_ids=[identity for identity in selected_ids if identity not in supplied],
            ))
        trace.total_seconds = perf_counter() - started
        if checkpoint:
            checkpoint()
        return PlannedEvidence(evidence=evidence, trace=trace)

def resolve_ready_scope(
    question: str, session: Session, *, file_ids: list[str] | None = None,
    scope_question: str | None = None, allowed_file_ids: list[str] | None = None,
) -> tuple[dict[str, File], DocumentScope | None]:
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


def _configured_retriever(embedding_client, vector_store, top_k=DEFAULT_TOP_K, *,
                          evidence_max_tokens=DEFAULT_EVIDENCE_MAX_TOKENS,
                          encoding_name=DEFAULT_CHUNK_TOKENIZER, retrieval_options=None, reranker_client=None):
    options = retrieval_options or RetrievalOptions()
    reranker = Reranker(reranker_client, candidate_limit=options.rerank_candidate_limit,
                       max_input_tokens=options.rerank_max_input_tokens, encoding_name=encoding_name) if reranker_client is not None else None
    return Retriever(embedding_client, vector_store, top_k=top_k, evidence_max_tokens=evidence_max_tokens,
                     encoding_name=encoding_name, options=options, reranker=reranker)


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
    retriever = _configured_retriever(embedding_client, vector_store, top_k,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client)
    return retriever.retrieve(question, session, file_ids=file_ids, scope_question=scope_question)


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
    retriever = _configured_retriever(embedding_client, vector_store, top_k,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client)
    return retriever.retrieve_candidates(question, session, file_ids=file_ids, scope_question=scope_question, allowed_file_ids=allowed_file_ids, prioritize_scope=prioritize_scope)


def pack_retrieval_candidates(child_hits, session, diagnostics):
    return Retriever(None, None).pack(child_hits, session, diagnostics)
