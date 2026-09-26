"""Shared application resources and their FastAPI dependency."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.services.pdf import LocalPdfParser
from knowledgebase.providers.planner import PlannerClient


@dataclass
class AppResources:
    sessions: sessionmaker[Session]
    embeddings: EmbeddingClient
    store: ChromaStore
    llm: LLMClient
    streaming_llm: StreamingLLMClient
    settings: Settings
    resolver_llm: LLMClient | None = None
    reranker: RerankerClient | None = None
    assets: PdfAssets | None = None
    pdf_parser: LocalPdfParser | None = None
    planner: PlannerClient | None = None


def get_resources(request: Request) -> AppResources:
    return request.app.state.resources


Resources = Annotated[AppResources, Depends(get_resources)]
