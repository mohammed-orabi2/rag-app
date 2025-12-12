from app.db.schemas.Message import Message
from bson import ObjectId
from datetime import datetime
from app.db.repositories.message_repository import MessageRepository


class MessageManager(MessageRepository):
    def send_message(
        self,
        message_repo: MessageRepository,
        conversation_id: str,
        role: str,
        content: str,
        langsmith_run_id: str = None,
        workflow_metadata: dict = None,
        summary: str = None,
        rewritten_query: str = None,
    ) -> str:
        """Add a message to a conversation."""
        return message_repo.create_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            langsmith_run_id=langsmith_run_id,
            workflow_metadata=workflow_metadata,
            summary=summary,
            rewritten_query=rewritten_query,
        )

    def get_message_count(
        self, conversation_id: str, message_repo: MessageRepository
    ) -> int:
        """Get total number of messages in a conversation."""
        return message_repo.count_messages(conversation_id)

    def update_message_summary(
        self, message_id: str, summary: str, message_repo: MessageRepository
    ) -> bool:
        """Update a message with its summary."""
        return message_repo.update_summary(message_id, summary)

    def update_message_content(
        self, message_id: str, content: str, message_repo: MessageRepository
    ) -> bool:
        """Update a message with new content (e.g., rewritten query)."""
        return message_repo.update_content(message_id, content)

    def update_message_rewritten_query(
        self, message_id: str, rewritten_query: str, message_repo: MessageRepository
    ) -> bool:
        """Update a message with its rewritten query."""
        return message_repo.update_rewritten_query(message_id, rewritten_query)

    def get_conversation_messages(
        self, conversation_id: str, message_repo: MessageRepository
    ) -> list:
        """Get all messages for a conversation."""
        return message_repo.find_all(conversation_id)
