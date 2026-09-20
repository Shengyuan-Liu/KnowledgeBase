"""Create the knowledge-base API and own its application resources."""

from contextlib import asynccontextmanager
from pathlib import Path

import chromadb
from fastapi import FastAPI
from openai import AsyncOpenAI, OpenAI

from knowledgebase.api.chat import ChatResources, router as chat_router
from knowledgebase.api.conversations import router as conversations_router
from knowledgebase.api.files import FileResources, router as files_router
from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.storage.database import build_engine, build_session_factory, init_db
from knowledgebase.storage.vectordb import ChromaStore


def create_app(data_dir: Path | None = None) -> FastAPI:
    """Build the app; open databases and the provider client only at startup."""
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = Settings()
        directory = (data_dir if data_dir is not None else settings.data_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        engine = build_engine(f"sqlite:///{directory / 'knowledgebase.db'}")
        try:
            init_db(engine)
            collection = chromadb.PersistentClient(path=str(directory / "chroma")).get_or_create_collection(
                name="knowledgebase-chunks", embedding_function=None,
                configuration={"hnsw": {"space": "cosine"}},
            )
            with OpenAI(api_key=settings.openai_api_key) as sdk:
                app.state.file_resources = FileResources(
                    sessions=build_session_factory(engine),
                    embeddings=EmbeddingClient(sdk),
                    store=ChromaStore(collection),
                )
                files = app.state.file_resources
                async with AsyncOpenAI(api_key=settings.openai_api_key) as streaming_sdk:
                    app.state.chat_resources = ChatResources(
                        sessions=files.sessions,
                        embeddings=files.embeddings,
                        store=files.store,
                        llm=LLMClient(sdk, model="gpt-4.1-nano"),
                        streaming_llm=StreamingLLMClient(streaming_sdk, model="gpt-4.1-nano"),
                    )
                    yield
        finally:
            engine.dispose()

    app = FastAPI(title="KnowledgeBase", lifespan=lifespan)
    app.include_router(files_router)
    app.include_router(chat_router)
    app.include_router(conversations_router)
    return app
