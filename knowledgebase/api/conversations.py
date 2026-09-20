"""Read saved messages and their original answer evidence."""

from fastapi import APIRouter, HTTPException

from knowledgebase.api.dependencies import Resources
from knowledgebase.schemas import ConversationDetail
from knowledgebase.storage.operations import get_conversation_detail


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=ConversationDetail, responses={
    404: {"description": "Conversation not found"},
})
def read_conversation(conversation_id: str, resources: Resources):
    with resources.sessions() as session:
        conversation = get_conversation_detail(session, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation
