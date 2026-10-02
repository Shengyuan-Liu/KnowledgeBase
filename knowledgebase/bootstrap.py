"""Assemble reusable application components independently of HTTP and CLI entry points."""

from dataclasses import dataclass, field
from pathlib import Path

from openai import AsyncOpenAI, OpenAI
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.config import Settings
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.providers.planner import PlannerClient
from knowledgebase.providers.reranker import RerankerClient
from knowledgebase.rag.client import RagClient
from knowledgebase.rag.document_chunker import DocumentChunker
from knowledgebase.rag.parsing import DocumentParser
from knowledgebase.rag.pdf_runtime import LocalPdfParser
from knowledgebase.rag.reranking import Reranker
from knowledgebase.rag.retrieval import Retriever
from knowledgebase.services.chat import ChatService
from knowledgebase.services.files import FileService
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.vectordb import ChromaStore


@dataclass
class AppResources:
    """One object graph per runtime; constructor inputs are fixed after assembly."""

    sessions: sessionmaker[Session]
    embeddings: EmbeddingClient
    store: ChromaStore
    llm: LLMClient
    streaming_llm: StreamingLLMClient | None
    settings: Settings
    resolver_llm: LLMClient | None = None
    reranker: RerankerClient | None = None
    assets: PdfAssets | None = None
    pdf_parser: LocalPdfParser | None = None
    planner: PlannerClient | None = None
    files: FileService = field(init=False)
    retriever: Retriever = field(init=False)
    rag: RagClient = field(init=False)
    chat: ChatService = field(init=False)

    def __post_init__(self):
        settings = self.settings
        self.files = FileService(
            self.sessions,
            self.store,
            embeddings=self.embeddings,
            assets=self.assets,
            parser=DocumentParser(self.pdf_parser),
            chunker=DocumentChunker(
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
                chunking_strategy=settings.chunking_strategy,
                chunk_max_tokens=settings.chunk_max_tokens,
                chunk_tokenizer=settings.chunk_tokenizer,
                parent_max_tokens=settings.parent_max_tokens,
                semantic_similarity_threshold=settings.semantic_similarity_threshold,
                semantic_batch_size=settings.semantic_batch_size,
                embedding_model=settings.embedding_model,
                embeddings=self.embeddings,
            ),
        )
        self.retriever = Retriever(
            self.embeddings,
            self.store,
            top_k=settings.retrieval_top_k,
            evidence_max_tokens=settings.evidence_max_tokens,
            encoding_name=settings.chunk_tokenizer,
            options=settings.retrieval_options,
            reranker=Reranker(
                self.reranker,
                candidate_limit=settings.rerank_candidate_limit,
                max_input_tokens=settings.rerank_max_input_tokens,
                encoding_name=settings.chunk_tokenizer,
            )
            if self.reranker is not None
            else None,
        )
        self.rag = RagClient(
            self.sessions,
            self.retriever,
            self.llm,
            self.streaming_llm,
            planner=self.planner,
            planning_options=settings.planning,
            retrieval_mode=settings.retrieval_mode,
        )
        self.chat = ChatService(
            self.sessions,
            self.rag,
            resolver=self.resolver_llm,
            history_limit=settings.history_limit,
        )


def build_resources(
    settings: Settings,
    sessions: sessionmaker[Session],
    store: ChromaStore,
    sdk: OpenAI,
    streaming_sdk: AsyncOpenAI | None = None,
    *,
    data_dir: Path | None = None,
) -> AppResources:
    """Build services inside the caller's storage/SDK contexts and recover its library."""
    llm = LLMClient(
        sdk, model=settings.answer_model, reasoning_effort=settings.answer_reasoning_effort
    )
    resources = AppResources(
        settings=settings,
        sessions=sessions,
        store=store,
        embeddings=EmbeddingClient(sdk, model=settings.embedding_model),
        llm=llm,
        streaming_llm=StreamingLLMClient(
            streaming_sdk,
            model=settings.answer_model,
            reasoning_effort=settings.answer_reasoning_effort,
        )
        if streaming_sdk is not None
        else None,
        resolver_llm=LLMClient(sdk, model=settings.resolver_model)
        if settings.resolver_model
        else None,
        reranker=RerankerClient(
            settings.rerank_model,
            device=settings.rerank_device,
            batch_size=settings.rerank_batch_size,
            max_pair_tokens=settings.rerank_max_pair_tokens,
        )
        if settings.rerank_enabled
        else None,
        planner=PlannerClient(
            sdk,
            settings.planner_model or settings.answer_model,
            settings.planning,
            settings.chunk_tokenizer,
        ),
        assets=PdfAssets(data_dir if data_dir is not None else settings.data_dir),
        pdf_parser=LocalPdfParser(settings.pdf_model_dir),
    )
    resources.files.recover()
    return resources
