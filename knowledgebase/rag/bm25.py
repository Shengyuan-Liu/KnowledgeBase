"""Stateless lexical ranking over supplied canonical child or legacy flat chunks."""

from collections import Counter
from collections.abc import Sequence
from math import log1p
import re

from knowledgebase.config import DEFAULT_BM25_B, DEFAULT_BM25_K1, DEFAULT_TOP_K
from knowledgebase.schemas import BM25Match, Chunk


_TERMS = re.compile(r"\d+(?:\.\d+)+|[^\W_]+")


def tokenize(text: str) -> list[str]:
    """Case-fold words, split identifier punctuation, and keep decimal numbers.

    DS-GA 1002 becomes ds/ga/1002; ANTHROPIC_API_KEY becomes anthropic/api/key.
    No stemming, stop-word removal, or changes to the canonical source are made.
    """
    return _TERMS.findall(text.casefold())


def search_bm25(
    question: str,
    chunks: Sequence[Chunk],
    top_k: int = DEFAULT_TOP_K,
    *,
    k1: float = DEFAULT_BM25_K1,
    b: float = DEFAULT_BM25_B,
) -> list[BM25Match]:
    """Score lexical matches with positive BM25 IDF and return at most top_k.

    The caller supplies unique chunks from eligible files before ranking. Corpus
    statistics are rebuilt from their text on every call; tokenless chunks do not
    contribute. Query terms count once each. Only matching chunks are returned,
    ordered by descending score and then chunk ID, with contiguous one-based ranks.
    No storage, parent expansion, embedding request, or index mutation occurs here.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive.")
    if not 0 <= k1 < float("inf"):
        raise ValueError("k1 must be finite and nonnegative.")
    if not 0 <= b <= 1:
        raise ValueError("b must be between zero and one.")

    terms = sorted(set(tokenize(question)))
    if not terms:
        return []
    documents = []
    for chunk in chunks:
        counts = Counter(tokenize(chunk.text))
        if counts:
            documents.append((chunk.chunk_id, counts, counts.total()))
    if not documents:
        return []

    average_length = sum(length for _, _, length in documents) / len(documents)
    frequencies = Counter(term for _, counts, _ in documents for term in counts)
    idf = {
        term: log1p((len(documents) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
        for term in terms
    }
    scores = []
    for chunk_id, counts, length in documents:
        normalization = k1 * (1 - b + b * length / average_length)
        score = sum(
            idf[term] * counts[term] * (k1 + 1) / (counts[term] + normalization)
            for term in terms if counts[term]
        )
        if score > 0:
            scores.append((chunk_id, score))
    scores.sort(key=lambda item: (-item[1], item[0]))
    return [
        BM25Match(chunk_id=chunk_id, score=score, rank=rank)
        for rank, (chunk_id, score) in enumerate(scores[:top_k], start=1)
    ]
