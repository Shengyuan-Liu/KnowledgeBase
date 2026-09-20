"""Coordinate retrieval and generation for one knowledge-base question."""

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import generate_answer
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.schemas import AnswerSource, ChatAnswer
from knowledgebase.storage.operations import get_files
from knowledgebase.storage.vectordb import ChromaStore


def answer_question(
    question: str,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    llm_client: LLMClient,
    top_k: int = 5,
) -> ChatAnswer:
    """Return an answer and sources in the same order used by the prompt.

    The service owns its read session and closes it before generation. Sources
    include every retrieved excerpt, regardless of which ones the model cites.
    Source IDs are one-based and local to this answer.
    """
    with session_factory() as session:
        chunks = retrieve(
            question, session, embedding_client, vector_store, top_k=top_k
        )
        files_by_id = {file.file_id: file for file in get_files(session)}
        sources = [
            AnswerSource(
                source_id=number,
                file_id=item.chunk.file_id,
                file_name=files_by_id[item.chunk.file_id].file_name,
                chunk_id=item.chunk.chunk_id,
                text=item.chunk.text,
                distance=item.distance,
            )
            for number, item in enumerate(chunks, start=1)
        ]

    answer = generate_answer(question, chunks, llm_client)
    return ChatAnswer(answer=answer, sources=sources)
