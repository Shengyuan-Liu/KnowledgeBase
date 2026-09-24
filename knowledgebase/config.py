"""Central defaults and runtime configuration for the API, CLI, and evaluations."""

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Pure functions use these defaults without reading .env or requiring credentials.
# Entry points load Settings once and explicitly pass the resolved values onward.
DEFAULT_ANSWER_MODEL = "gpt-4.1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 2048
DEFAULT_OVERLAP = 256
DEFAULT_CHUNKING_STRATEGY = "parent_child"
DEFAULT_CHUNK_MAX_TOKENS = 512
DEFAULT_CHUNK_TOKENIZER = "cl100k_base"
DEFAULT_PARENT_MAX_TOKENS = 1536
DEFAULT_EVIDENCE_MAX_TOKENS = 4096
DEFAULT_EVIDENCE_PACKING_STRATEGY = "parent_then_child"
DEFAULT_BM25_K1 = 1.2
DEFAULT_BM25_B = 0.75
DEFAULT_RRF_K = 60
DEFAULT_RRF_LIMIT = 20
DEFAULT_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_RERANK_CANDIDATE_LIMIT = 20
DEFAULT_RERANK_MAX_INPUT_TOKENS = 16384
DEFAULT_TOP_K = 5
DEFAULT_HISTORY_LIMIT = 10


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
    rerank_candidate_limit: int = Field(default=DEFAULT_RERANK_CANDIDATE_LIMIT, gt=0)
    rerank_max_input_tokens: int = Field(default=DEFAULT_RERANK_MAX_INPUT_TOKENS, gt=0)

    @model_validator(mode="after")
    def valid_rerank_strategy(self) -> Self:
        if self.rerank_enabled and self.strategy != "hybrid":
            raise ValueError("Reranking requires hybrid retrieval.")
        return self


class Settings(BaseSettings):
    """Read .env from the working directory; environment variables take precedence."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True,
        hide_input_in_errors=True,
    )

    openai_api_key: str = Field(repr=False)
    openai_base_url: str | None = None
    openai_timeout_seconds: float = Field(default=600, gt=0)
    openai_max_retries: int = Field(default=2, ge=0)
    data_dir: Path = Path("data/v1")

    answer_model: str = DEFAULT_ANSWER_MODEL
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    resolver_model: str | None = None
    rerank_model: str = DEFAULT_RERANK_MODEL
    rerank_device: Literal["auto", "cpu", "mps", "cuda"] = "auto"
    rerank_batch_size: int = Field(default=4, gt=0)
    rerank_max_pair_tokens: int = Field(default=1024, gt=0)
    rerank_enabled: bool = False
    rerank_candidate_limit: int = Field(default=DEFAULT_RERANK_CANDIDATE_LIMIT, gt=0)
    rerank_max_input_tokens: int = Field(default=DEFAULT_RERANK_MAX_INPUT_TOKENS, gt=0)
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, gt=0)
    chunk_overlap: int = Field(default=DEFAULT_OVERLAP, ge=0)
    chunking_strategy: Literal["structural", "character", "parent_child"] = DEFAULT_CHUNKING_STRATEGY
    chunk_max_tokens: int = Field(default=DEFAULT_CHUNK_MAX_TOKENS, gt=0)
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER
    parent_max_tokens: int = Field(default=DEFAULT_PARENT_MAX_TOKENS, gt=0)
    evidence_max_tokens: int = Field(default=DEFAULT_EVIDENCE_MAX_TOKENS, gt=0)
    evidence_packing_strategy: Literal["parent_then_child", "parent_first"] = DEFAULT_EVIDENCE_PACKING_STRATEGY
    retrieval_top_k: int = Field(default=DEFAULT_TOP_K, gt=0)
    retrieval_strategy: Literal["vector", "hybrid"] = "hybrid"
    retrieval_candidate_limit: int = Field(default=DEFAULT_RRF_LIMIT, gt=0)
    bm25_k1: float = Field(default=DEFAULT_BM25_K1, ge=0, allow_inf_nan=False)
    bm25_b: float = Field(default=DEFAULT_BM25_B, ge=0, le=1, allow_inf_nan=False)
    rrf_k: float = Field(default=DEFAULT_RRF_K, ge=0, allow_inf_nan=False)
    history_limit: int = Field(default=DEFAULT_HISTORY_LIMIT, gt=0)

    # Evaluations retain their shorter timeout and disabled retries.
    eval_timeout_seconds: float = Field(default=60, gt=0)
    eval_max_retries: int = Field(default=0, ge=0)
    judge_model: str = "gpt-5.4-mini"
    judge_reasoning_effort: Literal["off", "none", "low", "medium", "high", "xhigh"] = "medium"
    judge_timeout_seconds: float = Field(default=180, gt=0)
    judge_concurrency: int = Field(default=4, gt=0)

    @property
    def retrieval_options(self) -> RetrievalOptions:
        return RetrievalOptions(
            strategy=self.retrieval_strategy, candidate_limit=self.retrieval_candidate_limit,
            packing_strategy=self.evidence_packing_strategy,
            bm25_k1=self.bm25_k1, bm25_b=self.bm25_b, rrf_k=self.rrf_k,
            rerank_enabled=self.rerank_enabled, rerank_candidate_limit=self.rerank_candidate_limit,
            rerank_max_input_tokens=self.rerank_max_input_tokens,
        )

    @model_validator(mode="after")
    def valid_chunk_budgets(self) -> Self:
        if self.rerank_enabled and self.retrieval_strategy != "hybrid":
            raise ValueError("RERANK_ENABLED requires RETRIEVAL_STRATEGY=hybrid.")
        if self.chunking_strategy == "character" and self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        if self.chunking_strategy == "parent_child":
            if self.chunk_max_tokens > self.parent_max_tokens:
                raise ValueError("CHUNK_MAX_TOKENS must not exceed PARENT_MAX_TOKENS.")
            if self.parent_max_tokens >= self.evidence_max_tokens:
                raise ValueError("PARENT_MAX_TOKENS must be smaller than EVIDENCE_MAX_TOKENS to leave room for citation labels.")
        return self
