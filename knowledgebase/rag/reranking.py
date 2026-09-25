"""Score a bounded RRF window before selecting children for parent expansion."""

from collections.abc import Sequence

import tiktoken

from knowledgebase.config import (
    DEFAULT_CHUNK_TOKENIZER, DEFAULT_RERANK_CANDIDATE_LIMIT,
    DEFAULT_RERANK_MAX_INPUT_TOKENS, DEFAULT_TOP_K,
)
from knowledgebase.providers.reranker import RerankerClient, build_rerank_pairs
from knowledgebase.schemas import FusedMatch, RerankCandidate, RerankedMatch, RerankResult


INPUT_FORMAT_VERSION = "cross-encoder-pairs-v1"


def rerank(
    question: str, candidates: Sequence[RerankCandidate], client: RerankerClient,
    top_k: int = DEFAULT_TOP_K, *, candidate_limit: int = DEFAULT_RERANK_CANDIDATE_LIMIT,
    max_input_tokens: int = DEFAULT_RERANK_MAX_INPUT_TOKENS,
    encoding_name: str = DEFAULT_CHUNK_TOKENIZER,
) -> RerankResult:
    """Score the leading RRF window, retain all scores, and expose selected top-k.

    Ties retain RRF rank, then chunk ID. The input-text budget counts question/passage
    pair text, including repeated questions and heading prefixes. Oversized input
    fails before a call; it is never truncated.
    The caller supplies eligible, uniquely identified child or legacy flat hits.
    This module does not query storage, expand parents, or generate an answer.
    """
    if top_k <= 0 or candidate_limit <= 0 or max_input_tokens <= 0:
        raise ValueError("Rerank selection, candidate, and input-token limits must be positive.")
    if len({candidate.chunk_id for candidate in candidates}) != len(candidates):
        raise ValueError("Rerank candidate IDs must be unique.")
    window = sorted(candidates, key=lambda candidate: (candidate.rank, candidate.chunk_id))[:candidate_limit]
    result = RerankResult(
        question=question, model=client.model, prompt_version=INPUT_FORMAT_VERSION, score_kind="logit",
        model_revision=client.model_revision, device=client.device,
        max_pair_tokens=client.max_pair_tokens, batch_size=client.batch_size,
        tokenizer=encoding_name, input_tokens=0, candidate_limit=candidate_limit,
        max_input_tokens=max_input_tokens, top_k=top_k, candidates=window, matches=[],
    )
    if not window:
        return result
    pairs = build_rerank_pairs(question, window)
    encoding = tiktoken.get_encoding(encoding_name)
    result.input_tokens = sum(len(encoding.encode_ordinary(text)) for pair in pairs for text in pair)
    if result.input_tokens > max_input_tokens:
        raise ValueError("Rerank input exceeds max_input_tokens; no text was truncated.")
    scores = client.score(question, window)
    expected_ids = {candidate.chunk_id for candidate in window}
    if len(scores) != len(window) or {score.chunk_id for score in scores} != expected_ids:
        raise ValueError("Reranker must score every supplied chunk ID exactly once.")
    by_id = {score.chunk_id: score.score for score in scores}
    ordered = sorted(window, key=lambda candidate: (-by_id[candidate.chunk_id], candidate.rank, candidate.chunk_id))
    result.matches = [
        RerankedMatch(
            **candidate.model_dump(include=set(FusedMatch.model_fields)),
            rerank_score=by_id[candidate.chunk_id], rerank_rank=rank, score_kind="logit",
            scoring_parent_id=candidate.scoring_parent_id,
        )
        for rank, candidate in enumerate(ordered, start=1)
    ]
    return result
