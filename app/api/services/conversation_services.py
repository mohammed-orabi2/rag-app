from typing import Dict, List, Optional, Any
from app.db.repositories.conversation_repository import ConversationRepository
from app.core.agents.llms import llm_google_flash
from app.api.services.message_services import MessageService
from app.core.src.prompts import pull_prompt_from_langsmith
from langsmith.run_helpers import tracing_context


class ConversationService:
    """Service for conversation operations."""

    def __init__(self, conversation_repository: ConversationRepository = None):
        """Initialize with repository or create a new one if not provided."""
        self.conversation_repository = (
            conversation_repository or ConversationRepository()
        )

    async def create_conversation(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new conversation.

        Args:
            user_id: ID of the user creating the conversation
            title: Title for the conversation

        Returns:
            Dictionary with operation result and conversation ID
        """
        try:
            # Create conversation data dictionary
            conversation_data = {"user_id": user_id}

            conversation_id = await self.conversation_repository.create(
                conversation_data
            )

            if conversation_id:
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "message": "Conversation created successfully",
                }
            else:
                return {
                    "success": False,
                    "conversation_id": None,
                    "message": "Failed to create conversation",
                }
        except Exception as e:
            return {
                "success": False,
                "conversation_id": None,
                "message": f"Error creating conversation: {str(e)}",
            }

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by its ID.

        Args:
            conversation_id: ID of the conversation to retrieve

        Returns:
            Conversation data or None if not found
        """
        conversation = await self.conversation_repository.find_by_id(conversation_id)
        if conversation:
            return {"success": True, "conversation": conversation}
        return {"success": False, "message": "Conversation not found"}

    async def update_conversation(
        self, conversation_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a conversation.

        Args:
            conversation_id: ID of the conversation to update
            update_data: Data to update in the conversation

        Returns:
            Dictionary with operation result
        """
        result = await self.conversation_repository.update(conversation_id, update_data)

        if result:
            return {"success": True, "message": "Conversation updated successfully"}
        else:
            return {"success": False, "message": "Failed to update conversation"}

    async def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            Dictionary with operation result
        """
        result = await self.conversation_repository.delete(conversation_id)

        if result:
            return {"success": True, "message": "Conversation deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete conversation"}

    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of conversations for the user
        """
        conversations = await self.conversation_repository.find_all(user_id)
        return conversations if conversations else []

    async def update_conversation_title(
        self, conversation_id: str, title: str
    ) -> Dict[str, Any]:
        """
        Update conversation title.

        Args:
            conversation_id: ID of the conversation
            title: New title for the conversation

        Returns:
            Dictionary with operation result
        """
        result = await self.conversation_repository.update_title(conversation_id, title)

        if result:
            return {
                "success": True,
                "message": "Conversation title updated successfully",
            }
        else:
            return {"success": False, "message": "Failed to update conversation title"}

    async def update_excluded_ids(
        self, conversation_id: str, excluded_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Update conversation excluded_ids.

        Args:
            conversation_id: ID of the conversation
            exclude_ids: List of document IDs to exclude from the conversation

        Returns:
            Dictionary with operation result
        """
        result = await self.conversation_repository.update_excluded_ids(
            conversation_id, excluded_ids
        )

        if result:
            return {
                "success": True,
                "message": "Conversation excluded IDs updated successfully",
            }
        else:
            return {
                "success": False,
                "message": "Failed to update conversation excluded IDs",
            }

    async def increment_message_count(self, conversation_id: str) -> Dict[str, Any]:
        """
        Increment message count for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Dictionary with operation result
        """
        result = await self.conversation_repository.increment_message_count(
            conversation_id
        )

        if result:
            return {
                "success": True,
                "message": "Message count incremented successfully",
            }
        else:
            return {"success": False, "message": "Failed to increment message count"}

    async def generate_new_title(self, conversation_id: str) -> Dict[str, Any]:
        """Generate new title for conversation based on message content."""
        try:
            message_service = MessageService()
            content = []

            # Get messages and handle potential errors
            messages = await message_service.get_conversation_messages(conversation_id)
            if not messages:
                return {
                    "success": True,
                    "title": "New Conversation",
                    "message": "No messages found",
                }

            # Extract user messages
            content = [
                message["content"]
                for message in messages
                if message.get("role") == "user"
            ][:4]

            if not content:
                return {
                    "success": True,
                    "title": "New Conversation",
                    "message": "No user messages found",
                }

            try:
                prompt = pull_prompt_from_langsmith("title-update-prompt")
                combined_prompt = prompt.format_messages(conversation_text=content)
                title = llm_google_flash.invoke(combined_prompt).content

                generated_title = (
                    title if title != "No Title Yet" else "New Conversation"
                )

                # Update the title in the database
                update_result = await self.update_conversation_title(
                    conversation_id, generated_title
                )

                if update_result["success"]:
                    return {
                        "success": True,
                        "title": generated_title,
                        "message": "Title generated and updated successfully",
                    }
                else:
                    return {
                        "success": False,
                        "title": None,
                        "message": "Failed to update title in database",
                    }

            except Exception as e:
                return {
                    "success": False,
                    "title": None,
                    "message": f"Error generating title: {str(e)}",
                }

        except Exception as e:
            return {
                "success": False,
                "title": None,
                "message": f"Error processing messages: {str(e)}",
            }
