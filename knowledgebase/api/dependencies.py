"""Shared application resources and their FastAPI dependency."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.storage.vectordb import ChromaStore


@dataclass
class AppResources:
    sessions: sessionmaker[Session]
    embeddings: EmbeddingClient
    store: ChromaStore
    llm: LLMClient
    streaming_llm: StreamingLLMClient


def get_resources(request: Request) -> AppResources:
    return request.app.state.resources


Resources = Annotated[AppResources, Depends(get_resources)]
