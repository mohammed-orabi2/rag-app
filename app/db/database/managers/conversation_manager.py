from typing import List, Optional
from bson import ObjectId
from app.db.repositories.conversation_repository import ConversationRepository


class ConversationManager:

    def create_conversation(
        self,
        user_id: str,
        conversations_repo: ConversationRepository,
        title: str = None,
    ) -> dict:
        """Create conversation and return structured result."""
        return conversations_repo.create({"user_id": user_id, "title": title})

    def get_conversation(
        self, conversation_id: str, conversation_repo: ConversationRepository
    ) -> Optional[dict]:
        """Get conversation by ID."""
        return conversation_repo.find_by_id(conversation_id)

    def get_user_conversations(
        self, user_id: str, conversations_repo: ConversationRepository
    ) -> List[dict]:
        """Get all conversations for a user, sorted by most recent."""
        return conversations_repo.find_conversations(user_id)

    def update_conversation_title(
        self,
        conversation_id: str,
        title: str,
        conversations_repo: ConversationRepository,
    ) -> bool:
        """Update conversation title."""
        return conversations_repo.update_title(conversation_id, title)

    def update_conversation_excluded_ids(
        self,
        conversation_id: str,
        exclude_ids: List[str],
        conversations_repo: ConversationRepository,
    ) -> bool:
        """Update conversation exclude_ids."""
        return conversations_repo.update_excluded_ids(conversation_id, exclude_ids)

    def delete_conversation(
        self, conversation_id: str, conversations_repo: ConversationRepository
    ) -> bool:
        """Delete a conversation and all its messages."""
        return conversations_repo.delete(conversation_id)
        # return conversations_repo.delete(conversation_id, user_id)
