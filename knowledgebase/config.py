"""Central defaults and runtime configuration for the API, CLI, and evaluations."""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Pure functions use these defaults without reading .env or requiring credentials.
# Entry points load Settings once and explicitly pass the resolved values onward.
DEFAULT_ANSWER_MODEL = "gpt-4.1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 2048
DEFAULT_OVERLAP = 256
DEFAULT_CHUNKING_STRATEGY = "structural"
DEFAULT_CHUNK_MAX_TOKENS = 512
DEFAULT_CHUNK_TOKENIZER = "cl100k_base"
DEFAULT_PARENT_MAX_TOKENS = 1536
DEFAULT_EVIDENCE_MAX_TOKENS = 4096
DEFAULT_TOP_K = 5
DEFAULT_HISTORY_LIMIT = 10


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
    chunk_size: int = Field(default=DEFAULT_CHUNK_SIZE, gt=0)
    chunk_overlap: int = Field(default=DEFAULT_OVERLAP, ge=0)
    chunking_strategy: Literal["structural", "character", "parent_child"] = DEFAULT_CHUNKING_STRATEGY
    chunk_max_tokens: int = Field(default=DEFAULT_CHUNK_MAX_TOKENS, gt=0)
    chunk_tokenizer: str = DEFAULT_CHUNK_TOKENIZER
    parent_max_tokens: int = Field(default=DEFAULT_PARENT_MAX_TOKENS, gt=0)
    evidence_max_tokens: int = Field(default=DEFAULT_EVIDENCE_MAX_TOKENS, gt=0)
    retrieval_top_k: int = Field(default=DEFAULT_TOP_K, gt=0)
    history_limit: int = Field(default=DEFAULT_HISTORY_LIMIT, gt=0)

    # Evaluations retain their shorter timeout and disabled retries.
    eval_timeout_seconds: float = Field(default=60, gt=0)
    eval_max_retries: int = Field(default=0, ge=0)
    judge_model: str = "gpt-4.1-mini"

    @model_validator(mode="after")
    def valid_chunk_budgets(self) -> Self:
        if self.chunking_strategy == "character" and self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        if self.chunking_strategy == "parent_child":
            if self.chunk_max_tokens > self.parent_max_tokens:
                raise ValueError("CHUNK_MAX_TOKENS must not exceed PARENT_MAX_TOKENS.")
            if self.parent_max_tokens >= self.evidence_max_tokens:
                raise ValueError("PARENT_MAX_TOKENS must be smaller than EVIDENCE_MAX_TOKENS to leave room for citation labels.")
        return self
