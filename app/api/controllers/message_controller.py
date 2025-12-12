from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from app.api.schemas.schema import StandardResponse, MessageCreate
from utils.logging_info import get_logger
from app.api.services.message_services import MessageService
from app.api.services.chat_service import ChatService
import json

logger = get_logger()
router = APIRouter()

message_service = MessageService()


@router.get(
    "/conversations/{conversation_id}/messages", response_model=StandardResponse
)
async def get_conversation_messages(conversation_id: str):
    """Get all messages for a conversation."""
    try:
        messages = await message_service.get_conversation_messages(conversation_id)

        return StandardResponse(
            success=True,
            message="Messages retrieved successfully",
            data={"messages": messages},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_conversation_messages endpoint: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message(conversation_id: str, message_data: MessageCreate):
    """Stream a message response from a conversation using the chat service."""

    chat_service = ChatService(conversation_id)
    try:
        if not message_data.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content required",
            )

        async def response_generator_with_run_id():
            run_id = None
            try:
                async for chunk in chat_service.stream_chat(
                    user_input=message_data.content,
                    username=message_data.username,
                ):
                    if chunk.startswith("data: {") and "run_id" in chunk:
                        try:
                            # Extract the JSON data from the SSE format
                            json_str = chunk.replace("data: ", "").strip()
                            data = json.loads(json_str)
                            if "run_id" in data:
                                run_id = data["run_id"]
                        except:
                            pass

                    yield chunk

            except Exception as e:
                logger.error("Error during streaming: %s", e)
                error_data = {
                    "error": "Stream interrupted",
                    "message": str(e),
                    "run_id": run_id,
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            response_generator_with_run_id(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in stream_message endpoint: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
