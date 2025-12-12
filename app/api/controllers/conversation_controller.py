from fastapi import APIRouter, HTTPException, status, Query
from app.api.schemas.schema import StandardResponse  # Add ConversationCreate import
from utils.logging_info import get_logger
from app.api.services.conversation_services import ConversationService
from app.api.services.user_services import UserService

logger = get_logger()
router = APIRouter()

conversation_service = ConversationService()
user_service = UserService()


@router.post("/conversations", response_model=StandardResponse)
async def create_conversation(
    user_id: str = Query(
        ..., description="Your User ID"
    ),  # Make user_id optional with default
):
    """Create a new conversation."""

    result = await conversation_service.create_conversation(user_id)
    if result["success"]:
        return StandardResponse(
            success=True,
            message=result["message"],
            data={"conversation_id": result["conversation_id"]},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
        )


@router.get("/conversations", response_model=StandardResponse)
async def get_user_conversations(user_id: str = Query(..., description="Your User ID")):
    """Get all conversations for a user."""
    conversations = await conversation_service.get_user_conversations(user_id)

    return StandardResponse(
        success=True,
        message="Conversations retrieved successfully",
        data={"conversations": conversations},
    )


@router.get("/conversations/{conversation_id}", response_model=StandardResponse)
async def get_conversation(conversation_id: str):
    """Get a specific conversation."""

    conversation = await conversation_service.get_conversation(
        conversation_id
    )  # in facade

    if conversation:
        return StandardResponse(
            success=True,
            message="Conversation retrieved successfully",
            data={"conversation": conversation},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied",
        )


@router.delete("/conversations/{conversation_id}", response_model=StandardResponse)
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    result = await conversation_service.delete_conversation(conversation_id)

    if result["success"]:
        return StandardResponse(success=True, message=result["message"])
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=result["message"]
        )


@router.put("/conversations/{conversation_id}/title", response_model=StandardResponse)
async def update_conversation_title(
    conversation_id: str, user_id: str = Query(..., description="Your User ID")
):
    """Update conversation title automatically based on conversation content."""
    try:
        # Get user
        user_result = await user_service.get_user(user_id)
        if not user_result["success"]:
            return StandardResponse(success=False, message="User not found", data=None)

        # Generate new title
        result = await conversation_service.generate_new_title(conversation_id)

        if result["success"]:
            return StandardResponse(
                success=True, message=result["message"], data={"title": result["title"]}
            )
        else:
            return StandardResponse(success=False, message=result["message"], data=None)

    except Exception as e:
        logger.error(f"Error in update_conversation_title endpoint: {str(e)}")
        return StandardResponse(
            success=False, message="Error updating conversation title", data=None
        )
