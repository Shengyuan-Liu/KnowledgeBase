"""Execute independent queries, merge child ranks, then pack one evidence set."""

from time import perf_counter
from collections.abc import Callable
from sqlalchemy.orm import Session

from knowledgebase.config import (
    DEFAULT_TOP_K, DEFAULT_EVIDENCE_MAX_TOKENS, DEFAULT_CHUNK_TOKENIZER,
    DEFAULT_EVIDENCE_PACKING_STRATEGY, RetrievalOptions,
)
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.schemas import (
    PlannedQuery, RetrievalPlan, RetrievedChunk, RetrievedEvidence, RetrievalDiagnostics, QueryRun,
    QueryVote, MergedCandidate, PlanTrace, PlannedEvidence, RequirementEvidence,
)
from knowledgebase.storage.vectordb import ChromaStore


def merge_query_runs(runs: list[QueryRun], *, k: float) -> list[MergedCandidate]:
    """Equal-weight RRF across queries, separate from each query's route RRF.

    Identical trimmed query text contributes at most one vote per child, even if
    executed with different narrower scopes. Use its best rank across those runs.
    """
    votes: dict[str, dict[str, QueryVote]] = {}
    files = {}
    for run_index, run in enumerate(runs):
        for rank, hit in enumerate(run.result.chunks, start=1):
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
    """Reserve query-local leaders per requirement/document, then fill by RRF.

    A child with weak votes from many unrelated questions must not displace the
    best hit for an individual answer point.
    """
    selected: list[str] = []
    requirements = []
    for requirement in plan.requirements:
        ranks: dict[str, int] = {}
        for run in runs:
            if requirement.requirement_id in run.requirement_ids:
                for rank, hit in enumerate(run.result.chunks, start=1):
                    identity = hit.chunk.chunk_id
                    ranks[identity] = min(rank, ranks.get(identity, rank))
        groups: dict[str, list[str]] = {}
        eligible = [candidate for candidate in merged if candidate.chunk_id in ranks]
        for candidate in sorted(eligible, key=lambda c: (ranks[c.chunk_id], c.rank)):
            groups.setdefault(candidate.file_id, []).append(candidate.chunk_id)
        requirements.append(list(groups.values()))
    # Round-robin across requirements before taking another document for one.
    while len(selected) < top_k and any(requirements):
        for groups in requirements:
            while groups and groups[0][0] in selected:
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
    from knowledgebase.rag.retrieval import _configured_retriever

    retriever = _configured_retriever(embedding_client, vector_store, top_k,
        evidence_max_tokens=evidence_max_tokens, encoding_name=encoding_name,
        retrieval_options=retrieval_options, reranker_client=reranker_client)
    return retriever.retrieve_plan(plan, session, file_ids=file_ids, allowed_file_ids=allowed_file_ids,
        checkpoint=checkpoint, queries=queries, previous_runs=previous_runs, round_index=round_index)
