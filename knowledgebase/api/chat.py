"""Expose conversational answers through JSON and streamed HTTP endpoints."""

from fastapi import APIRouter, HTTPException

from knowledgebase.api.dependencies import Resources
from knowledgebase.api.streaming import ChatStreamingResponse
from knowledgebase.schemas import ChatRequest, ConversationAnswer, StreamChatRequest
from knowledgebase.services.chat import (
    ConversationNotFoundError, answer_in_conversation, stream_answer_in_conversation,
)


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
            top_k=resources.settings.retrieval_top_k, history_limit=resources.settings.history_limit,
            resolver_client=resources.resolver_llm,
            evidence_max_tokens=resources.settings.evidence_max_tokens,
            encoding_name=resources.settings.chunk_tokenizer,
            retrieval_options=resources.settings.retrieval_options,
        )
    except ConversationNotFoundError as error:
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
            top_k=resources.settings.retrieval_top_k, history_limit=resources.settings.history_limit,
            resolver_client=resources.resolver_llm,
            evidence_max_tokens=resources.settings.evidence_max_tokens,
            encoding_name=resources.settings.chunk_tokenizer,
            retrieval_options=resources.settings.retrieval_options,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Stream setup failed.") from error
    return ChatStreamingResponse(events)
