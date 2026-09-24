"""Create the knowledge-base API and own its application resources."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI, OpenAI

from knowledgebase.api.chat import router as chat_router
from knowledgebase.api.dependencies import AppResources
from knowledgebase.api.conversations import router as conversations_router
from knowledgebase.api.files import router as files_router
from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.storage.runtime import open_storage


def create_app(data_dir: Path | None = None, frontend_dir: Path | None = None) -> FastAPI:
    """Build the app; open databases and the provider client only at startup."""
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings = Settings()
        directory = data_dir if data_dir is not None else settings.data_dir
        sdk_options = dict(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds, max_retries=settings.openai_max_retries,
        )
        with open_storage(directory) as (sessions, store):
            with OpenAI(**sdk_options) as sdk:
                async with AsyncOpenAI(**sdk_options) as streaming_sdk:
                    app.state.resources = AppResources(
                        settings=settings,
                        reranker=RerankerClient(
                            settings.rerank_model, device=settings.rerank_device,
                            batch_size=settings.rerank_batch_size, max_pair_tokens=settings.rerank_max_pair_tokens,
                        ) if settings.rerank_enabled else None,
                        resolver_llm=LLMClient(sdk, model=settings.resolver_model) if settings.resolver_model else None,
                        sessions=sessions,
                        embeddings=EmbeddingClient(sdk, model=settings.embedding_model),
                        store=store,
                        llm=LLMClient(sdk, model=settings.answer_model),
                        streaming_llm=StreamingLLMClient(streaming_sdk, model=settings.answer_model),
                    )
                    yield

    app = FastAPI(title="KnowledgeBase", lifespan=lifespan)
    app.include_router(files_router)
    app.include_router(chat_router)
    app.include_router(conversations_router)
    frontend = frontend_dir if frontend_dir is not None else Path(__file__).resolve().parents[2] / "frontend/dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="workspace")
    return app
