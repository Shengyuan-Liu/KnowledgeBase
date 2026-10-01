"""Read saved messages and their original answer evidence."""

from fastapi import APIRouter, HTTPException

from knowledgebase.api.dependencies import Resources
from knowledgebase.schemas import ConversationDetail
from knowledgebase.services.chat import ConversationNotFoundError

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    responses={
        404: {"description": "Conversation not found"},
    },
)
def read_conversation(conversation_id: str, resources: Resources):
    try:
        return resources.chat.get_conversation(conversation_id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
