"""Shared application resources and their FastAPI dependency."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import Settings
from knowledgebase.services.files import FileService
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.storage.vectordb import ChromaStore
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.rag.pdf_runtime import LocalPdfParser
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

    @property
    def files(self) -> FileService:
        return FileService.from_settings(self.settings, self.sessions, self.embeddings, self.store,
                                         assets=self.assets, pdf_parser=self.pdf_parser)


def get_resources(request: Request) -> AppResources:
    return request.app.state.resources


Resources = Annotated[AppResources, Depends(get_resources)]
