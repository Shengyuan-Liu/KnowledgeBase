"""Expose completed conversational answers as JSON over HTTP."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from knowledgebase.schemas import ChatRequest, ConversationAnswer
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.storage.vectordb import ChromaStore


@dataclass
class ChatResources:
    sessions: sessionmaker[Session]
    embeddings: EmbeddingClient
    store: ChromaStore
    llm: LLMClient


def get_chat_resources(request: Request) -> ChatResources:
    return request.app.state.chat_resources


Resources = Annotated[ChatResources, Depends(get_chat_resources)]
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ConversationAnswer, responses={
    404: {"description": "Conversation not found"},
    500: {"description": "Answer processing failed"},
})
def chat(body: ChatRequest, resources: Resources):
    """Return the complete answer after the conversation exchange is saved."""
    try:
        return answer_in_conversation(
            body.question, resources.sessions, resources.embeddings,
            resources.store, resources.llm,
            conversation_id=body.conversation_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Answer processing failed.") from error
