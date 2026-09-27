"""Execute independent queries, merge child ranks, then pack one evidence set."""

from time import perf_counter
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from knowledgebase.config import (
    DEFAULT_TOP_K, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER,
    DEFAULT_EVIDENCE_PACKING_STRATEGY, RetrievalOptions,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.planning import PlannedQuery, RetrievalPlan
from knowledgebase.rag.retrieval import retrieve_candidates, resolve_ready_scope, pack_retrieval_candidates
from knowledgebase.schemas import (
    DocumentScope, RetrievedCandidates, RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics,
)
from knowledgebase.storage.vectordb import ChromaStore


class QueryRun(BaseModel):
    round_index: int = 1
    query_ids: list[str]
    requirement_ids: list[str]
    text: str
    requested_file_ids: list[str] | None
    result: RetrievedCandidates
    seconds: float


class QueryVote(BaseModel):
    run_index: int
    rank: int


class MergedCandidate(BaseModel):
    chunk_id: str
    file_id: str
    score: float
    rank: int
    votes: list[QueryVote]


class RequirementEvidence(BaseModel):
    """Retrieval attribution only; a hit does not prove semantic support."""
    requirement_id: str
    candidate_ids: list[str]
    selected_ids: list[str]
    supplied_ids: list[str]
    budget_excluded_ids: list[str]


class PlanTrace(BaseModel):
    version: Literal[1] = 1
    plan: RetrievalPlan
    allowed_file_ids: list[str]
    document_scope: DocumentScope | None
    cross_query_rrf_k: float
    per_query_limit: int
    top_k: int
    max_evidence_tokens: int
    runs: list[QueryRun] = Field(default_factory=list)
    merged: list[MergedCandidate] = Field(default_factory=list)
    selected_ids: list[str] = Field(default_factory=list)
    requirements: list[RequirementEvidence] = Field(default_factory=list)
    stop_reason: Literal["independent_queries_complete", "scope_unresolved", "no_ready_files"]
    scope_seconds: float = 0
    merge_seconds: float = 0
    total_seconds: float = 0


class PlannedEvidence(BaseModel):
    evidence: RetrievedEvidence
    trace: PlanTrace


def merge_query_runs(runs: list[QueryRun], *, k: float) -> list[MergedCandidate]:
    """Equal-weight RRF across queries, separate from each query's route RRF.

    Identical trimmed query text contributes at most one vote per child, even if
    executed with different narrower scopes. Use its best rank across those runs.
    """
    votes: dict[str, dict[str, QueryVote]] = {}
    files = {}
    for run_index, run in enumerate(runs):
        for rank, hit in enumerate(run.result.hits, start=1):
            identity = hit.chunk.chunk_id
            files[identity] = hit.chunk.file_id
            by_query = votes.setdefault(identity, {})
            key = run.text.strip()
            if key not in by_query or rank < by_query[key].rank:
                by_query[key] = QueryVote(run_index=run_index, rank=rank)
    scores = {identity: sum(1 / (k + vote.rank) for vote in by_query.values())
              for identity, by_query in votes.items()}
    return [MergedCandidate(chunk_id=identity, file_id=files[identity], score=scores[identity], rank=rank,
                            votes=list(votes[identity].values()))
            for rank, identity in enumerate(sorted(scores, key=lambda identity: (-scores[identity], identity)), start=1)]


def _select_representatives(merged: list[MergedCandidate], runs: list[QueryRun], plan: RetrievalPlan, top_k: int) -> list[str]:
    """Reserve hits for each requirement/document pair, then fill by merged rank."""
    selected: list[str] = []
    requirements = []
    for requirement in plan.requirements:
        eligible = {hit.chunk.chunk_id for run in runs if requirement.requirement_id in run.requirement_ids
                    for hit in run.result.hits}
        groups: dict[str, list[str]] = {}
        for candidate in merged:
            if candidate.chunk_id in eligible:
                groups.setdefault(candidate.file_id, []).append(candidate.chunk_id)
        requirements.append(list(groups.values()))
    # Round-robin across requirements before taking another document for one.
    while len(selected) < top_k and any(requirements):
        for groups in requirements:
            while groups and any(identity in selected for identity in groups[0]):
                groups.pop(0)
            if groups and len(selected) < top_k:
                selected.append(groups.pop(0)[0])
    for candidate in merged:
        if len(selected) == top_k:
            break
        if candidate.chunk_id not in selected:
            selected.append(candidate.chunk_id)
    return selected


def retrieve_plan(
    plan: RetrievalPlan, session: Session, embedding_client: EmbeddingClient,
    vector_store: ChromaStore, top_k: int = DEFAULT_TOP_K, *,
    evidence_max_tokens: int = DEFAULT_EVIDENCE_MAX_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
    retrieval_options: RetrievalOptions | None = None,
    reranker_client: RerankerClient | None = None,
    file_ids: list[str] | None = None,
    allowed_file_ids: list[str] | None = None,
    checkpoint: Callable[[], object] | None = None,
    queries: list[PlannedQuery] | None = None,
    previous_runs: list[QueryRun] | None = None,
    round_index: int = 1,
) -> PlannedEvidence:
    """Execute a caller-supplied plan without generation, retries or extra rounds.

    The caller owns the session and retains the returned JSON-serializable trace.
    Provider/schema errors propagate; no partial result is presented as success.
    """
    started = perf_counter()
    if checkpoint:
        checkpoint()
    if top_k <= 0 or evidence_max_tokens <= 0:
        raise ValueError("top_k and evidence_max_tokens must be positive.")
    options = retrieval_options or RetrievalOptions()
    options = options.model_copy(update={"packing_strategy": options.packing_strategy or DEFAULT_EVIDENCE_PACKING_STRATEGY})
    if options.rerank_enabled and reranker_client is None:
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
        run.result.hits = [hit for hit in run.result.hits if hit.chunk.file_id in ready]
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
            candidates = retrieve_candidates(
                query.text, session, embedding_client, vector_store, trace.per_query_limit,
                evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
                retrieval_options=options, reranker_client=reranker_client,
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
    trace.selected_ids = ([hit.chunk.chunk_id for hit in trace.runs[0].result.hits]
                          if plan.route == "direct" and len(trace.runs) == 1 else
                          _select_representatives(trace.merged, trace.runs, plan, top_k))
    merged_by_id = {candidate.chunk_id: candidate for candidate in trace.merged}
    selected: list[RetrievedChunk] = []
    for identity in trace.selected_ids:
        vote = min(merged_by_id[identity].votes, key=lambda vote: (vote.rank, vote.run_index))
        result = trace.runs[vote.run_index].result
        selected.append(next(hit for hit in result.hits if hit.chunk.chunk_id == identity).model_copy(deep=True))
        diagnostics.candidates.append(next(candidate for candidate in result.diagnostics.candidates if candidate.chunk_id == identity))
    trace.merge_seconds = perf_counter() - merge_started
    if plan.route == "direct" and len(trace.runs) == 1:
        diagnostics = trace.runs[0].result.diagnostics.model_copy(deep=True)
    evidence = (pack_retrieval_candidates(selected, session, diagnostics) if ready else
                RetrievedEvidence(chunks=[], diagnostics=diagnostics))
    supplied = {hit.chunk.chunk_id for hit in evidence.chunks}
    supplied.update(identity for hit in evidence.chunks for identity in hit.matched_child_ids)
    for requirement in plan.requirements:
        candidates = {hit.chunk.chunk_id for run in trace.runs if requirement.requirement_id in run.requirement_ids
                      for hit in run.result.hits}
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
