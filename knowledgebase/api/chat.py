"""Expose conversational answers through JSON and streamed HTTP endpoints."""

from fastapi import APIRouter, HTTPException

from knowledgebase.api.dependencies import Resources
from knowledgebase.api.streaming import ChatStreamingResponse
from knowledgebase.schemas import ChatRequest, ConversationAnswer, StreamChatRequest
from knowledgebase.services.chat import (
    ConversationNotFoundError,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post(
    "",
    response_model=ConversationAnswer,
    responses={
        404: {"description": "Conversation not found"},
        500: {"description": "Answer processing failed"},
        504: {"description": "Planned request deadline reached"},
    },
)
def chat(body: ChatRequest, resources: Resources):
    """Return the complete answer after the conversation exchange is saved."""
    try:
        return resources.chat.answer(
            body.question,
            conversation_id=body.conversation_id,
            file_ids=body.file_ids,
            retrieval_mode=body.retrieval_mode,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except TimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail="The planned request timed out. Please retry or narrow the question.",
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Answer processing failed.") from error


@router.post(
    "/stream",
    response_class=ChatStreamingResponse,
    status_code=200,
    responses={
        404: {"description": "Conversation not found"},
        500: {"description": "Stream setup failed"},
    },
)
async def stream_chat(body: StreamChatRequest, resources: Resources):
    try:
        events = await resources.chat.stream(
            body.question,
            body.request_id,
            conversation_id=body.conversation_id,
            file_ids=body.file_ids,
            retrieval_mode=body.retrieval_mode,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Stream setup failed.") from error
    return ChatStreamingResponse(events)
