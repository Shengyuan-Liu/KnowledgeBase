"""Coordinate single-turn and conversational knowledge-base answers."""

from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.citations import validate_citations
from knowledgebase.rag.generation import generate_answer
from knowledgebase.rag.query import resolve_question
from knowledgebase.rag.retrieval import retrieve
from knowledgebase.schemas import AnswerSource, ChatAnswer, ConversationAnswer
from knowledgebase.storage.operations import (
    create_conversation,
    get_conversation,
    get_files,
    get_messages,
    save_message,
)
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
    return ChatAnswer(
        answer=answer, sources=sources,
        citation_check=validate_citations(answer, sources),
    )


def answer_in_conversation(
    question: str,
    session_factory: sessionmaker[Session],
    embedding_client: EmbeddingClient,
    vector_store: ChromaStore,
    llm_client: LLMClient,
    conversation_id: str | None = None,
    top_k: int = 5,
    history_limit: int = 10,
) -> ConversationAnswer:
    """Resolve a follow-up, retrieve fresh evidence, and save a completed exchange.

    Omit conversation_id to start a new conversation. A supplied ID must exist.
    Model calls run outside history/write sessions. Only successful exchanges
    are saved, with the original question and answer in one transaction.
    """
    if history_limit < 1:
        raise ValueError("history_limit must be positive.")
    history = []
    if conversation_id is not None:
        with session_factory() as session:
            if get_conversation(session, conversation_id) is None:
                raise LookupError(f"Conversation not found: {conversation_id}")
            history = get_messages(session, conversation_id, limit=history_limit)

    retrieval_question = resolve_question(question, history, llm_client)
    result = answer_question(
        retrieval_question, session_factory, embedding_client, vector_store,
        llm_client, top_k=top_k,
    )

    with session_factory.begin() as session:
        if conversation_id is None:
            conversation_id = uuid4().hex
            create_conversation(session, conversation_id)
        save_message(session, conversation_id, "user", question)
        message = save_message(session, conversation_id, "assistant", result.answer)

    return ConversationAnswer(
        answer=result.answer, sources=result.sources,
        citation_check=result.citation_check,
        conversation_id=conversation_id, message_id=message.message_id,
        question=question, retrieval_question=retrieval_question,
    )
