"""Expose conversational answers through JSON and streamed HTTP endpoints."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, sessionmaker

from knowledgebase.api.streaming import ChatStreamingResponse
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient, StreamingLLMClient
from knowledgebase.schemas import ChatRequest, ConversationAnswer, StreamChatRequest
from knowledgebase.services.chat import answer_in_conversation, stream_answer_in_conversation
from knowledgebase.storage.vectordb import ChromaStore


@dataclass
class ChatResources:
    sessions: sessionmaker[Session]
    embeddings: EmbeddingClient
    store: ChromaStore
    llm: LLMClient
    streaming_llm: StreamingLLMClient


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


@router.post("/stream", response_class=ChatStreamingResponse, status_code=200, responses={
    404: {"description": "Conversation not found"},
    500: {"description": "Stream setup failed"},
})
async def stream_chat(body: StreamChatRequest, resources: Resources):
    try:
        events = await stream_answer_in_conversation(
            body.question, body.request_id, resources.sessions, resources.embeddings,
            resources.store, resources.llm, resources.streaming_llm,
            conversation_id=body.conversation_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Stream setup failed.") from error
    return ChatStreamingResponse(events)
