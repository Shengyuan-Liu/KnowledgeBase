"""Explicit component options, independent of environment and credentials."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from knowledgebase.defaults import (
    DEFAULT_BM25_B,
    DEFAULT_BM25_K1,
    DEFAULT_RERANK_CANDIDATE_LIMIT,
    DEFAULT_RERANK_MAX_INPUT_TOKENS,
    DEFAULT_RRF_K,
    DEFAULT_RRF_LIMIT,
)


class RetrievalOptions(BaseModel):
    """Query-time retrieval controls, independent of credentials and .env."""

    strategy: Literal["vector", "hybrid"] = "hybrid"
    # Null in historical snapshots means that no packing strategy was recorded.
    packing_strategy: Literal["parent_then_child", "parent_first"] | None = None
    candidate_limit: int = Field(default=DEFAULT_RRF_LIMIT, gt=0)
    bm25_k1: float = Field(default=DEFAULT_BM25_K1, ge=0, allow_inf_nan=False)
    bm25_b: float = Field(default=DEFAULT_BM25_B, ge=0, le=1, allow_inf_nan=False)
    rrf_k: float = Field(default=DEFAULT_RRF_K, ge=0, allow_inf_nan=False)
    rerank_enabled: bool = False
    rerank_unit: Literal["child", "parent"] = "child"
    rerank_candidate_limit: int = Field(default=DEFAULT_RERANK_CANDIDATE_LIMIT, gt=0)
    rerank_max_input_tokens: int = Field(default=DEFAULT_RERANK_MAX_INPUT_TOKENS, gt=0)

    @model_validator(mode="after")
    def valid_rerank_strategy(self) -> Self:
        if self.rerank_enabled and self.strategy != "hybrid":
            raise ValueError("Reranking requires hybrid retrieval.")
        return self


class PlanningOptions(BaseModel):
    sufficiency_enabled: bool = True
    max_rounds: int = Field(default=3, ge=1, le=3)
    request_timeout_seconds: float = Field(default=180, gt=0)
    answer_reserve_seconds: float = Field(default=60, gt=0)
    planner_timeout_seconds: float = Field(default=30, gt=0)
    max_input_tokens: int = Field(default=8192, gt=0)
    max_output_tokens: int = Field(default=2048, gt=0)
    answer_max_input_tokens: int = Field(default=16384, gt=0)
    answer_max_output_tokens: int = Field(default=4096, gt=0)

    @model_validator(mode="after")
    def reserve_fits(self) -> Self:
        if self.answer_reserve_seconds >= self.request_timeout_seconds:
            raise ValueError(
                "The final-answer reserve must be smaller than the request deadline."
            )
        return self
