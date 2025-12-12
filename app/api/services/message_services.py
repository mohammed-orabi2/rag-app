"""
Message Services Module

This module provides service functions to handle operations related to messages.
It serves as an intermediary between the controllers and the repositories.
"""

from typing import Dict, List, Optional, Any
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.conversation_repository import ConversationRepository


class MessageService:
    """Service for message operations."""

    def __init__(
        self,
        message_repository: MessageRepository = None,
        conversation_repository: ConversationRepository = None,
    ):
        """Initialize with repositories or create new ones if not provided."""
        self.message_repository = message_repository or MessageRepository()
        self.conversation_repository = (
            conversation_repository or ConversationRepository()
        )

    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new message and increment the message count in the conversation.

        Args:
            message_data: Dictionary containing message information

        Returns:
            Dictionary with operation result and message ID
        """
        try:
            # Create the message
            message_id = await self.message_repository.create(message_data)

            if message_id:
                # Update message count in the conversation
                conversation_id = message_data.get("conversation_id")
                await self.conversation_repository.increment_message_count(
                    conversation_id
                )

                return {
                    "success": True,
                    "message_id": message_id,
                    "message": "Message created successfully",
                }
            else:
                return {
                    "success": False,
                    "message_id": None,
                    "message": "Failed to create message",
                }
        except Exception as e:
            return {
                "success": False,
                "message_id": None,
                "message": f"Error creating message: {str(e)}",
            }

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by its ID.

        Args:
            message_id: ID of the message to retrieve

        Returns:
            Message data or None if not found
        """
        return await self.message_repository.find_by_id(message_id)

    async def update_message(
        self, message_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a message.

        Args:
            message_id: ID of the message to update
            update_data: Data to update in the message

        Returns:
            Dictionary with operation result
        """
        result = await self.message_repository.update(message_id, update_data)

        if result:
            return {"success": True, "message": "Message updated successfully"}
        else:
            return {"success": False, "message": "Failed to update message"}

    async def delete_message(self, message_id: str) -> Dict[str, Any]:
        """
        Delete a message.

        Args:
            message_id: ID of the message to delete

        Returns:
            Dictionary with operation result
        """
        result = await self.message_repository.delete(message_id)

        if result:
            return {"success": True, "message": "Message deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete message"}

    async def get_conversation_messages(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of messages in the conversation
        """
        messages = await self.message_repository.find_all(conversation_id)
        return messages if messages else []

    async def update_message_content(
        self, message_id: str, content: str
    ) -> Dict[str, Any]:
        """
        Update message content.

        Args:
            message_id: ID of the message
            content: New content for the message

        Returns:
            Dictionary with operation result
        """
        result = await self.message_repository.update_content(message_id, content)

        if result:
            return {"success": True, "message": "Message content updated successfully"}
        else:
            return {"success": False, "message": "Failed to update message content"}

    async def update_message_summary(
        self, message_id: str, summary: str
    ) -> Dict[str, Any]:
        """
        Update message summary.

        Args:
            message_id: ID of the message
            summary: New summary for the message

        Returns:
            Dictionary with operation result
        """
        result = await self.message_repository.update_summary(message_id, summary)

        if result:
            return {"success": True, "message": "Message summary updated successfully"}
        else:
            return {"success": False, "message": "Failed to update message summary"}

    async def update_message_rewritten_query(
        self, message_id: str, rewritten_query: str
    ) -> Dict[str, Any]:
        """
        Update message rewritten query.

        Args:
            message_id: ID of the message
            rewritten_query: New rewritten query for the message

        Returns:
            Dictionary with operation result
        """
        result = await self.message_repository.update_rewritten_query(
            message_id, rewritten_query
        )

        if result:
            return {
                "success": True,
                "message": "Message rewritten query updated successfully",
            }
        else:
            return {
                "success": False,
                "message": "Failed to update message rewritten query",
            }

    async def count_messages(self, conversation_id: str) -> int:
        """
        Count messages in a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Number of messages in the conversation
        """
        return await self.message_repository.count_messages(conversation_id)

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        summary: Optional[str] = None,
        rewritten_query: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send a message by creating it in the database.

        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (user/assistant)
            content: Content of the message
            summary: Optional summary of the message
            rewritten_query: Optional rewritten query

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            message_data = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "summary": summary,
                "rewritten_query": rewritten_query,
            }

            message_id = await self.message_repository.create(message_data)

            if message_id:
                # Update message count in the conversation
                await self.conversation_repository.increment_message_count(
                    conversation_id
                )
                return message_id
            else:
                return None

        except Exception as e:
            return None
