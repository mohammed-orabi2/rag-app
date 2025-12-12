from typing import List, Optional, Dict, Any
from .interfaces.base_repo import IBaseRepository
from app.db.database.base_connection import BaseConnection
from bson import ObjectId
from datetime import datetime, timezone
from app.db.schemas import Conversation


class ConversationRepository(BaseConnection, IBaseRepository):
    """MongoDB implementation of conversation repository."""

    def __init__(self, db=None):
        super().__init__(db)

    async def _get_collection(self):
        """Get conversations collection."""
        database = await self.db
        return database["conversations"]

    # Base Repository Methods
    async def find_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Find conversation by ID."""
        try:
            print(f"🔍 DEBUG find_by_id: Looking for conversation {conversation_id}")
            conversations = await self._get_collection()
            conversation = await conversations.find_one(
                {"_id": ObjectId(conversation_id)}
            )
            if conversation:
                conversation["_id"] = str(conversation["_id"])
                return dict(conversation)
            else:
                print(
                    f"🔍 DEBUG find_by_id: No conversation found for {conversation_id}"
                )
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error finding conversation by ID {conversation_id}: {e}"
            )
            print(f"🔍 DEBUG find_by_id: Exception: {e}")
            return None

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new conversation and return structured result."""
        try:
            conversation = Conversation(
                user_id=data["user_id"],
                created_at=datetime.now(timezone.utc),
                message_count=0,
                last_message_at=None,
                last_message_timestamp=None,
                excluded_ids=[],
            )

            conversations = await self._get_collection()
            result = await conversations.insert_one(dict(conversation))

            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"[DATABASE] Error creating conversation: {e}")
            return None

    async def update(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        """Update conversation by ID."""
        try:
            conversations = await self._get_collection()
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)}, {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating conversation {conversation_id}: {e}"
            )
            return False

    async def delete(self, conversation_id: str) -> bool:
        """Delete conversation by ID."""
        try:
            conversations = await self._get_collection()
            result = await conversations.delete_one({"_id": ObjectId(conversation_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error deleting conversation {conversation_id}: {e}"
            )
            return False

    # Conversation-specific Methods
    async def find_all(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        try:
            conversations_collection = await self._get_collection()
            # Use string comparison instead of ObjectId
            cursor = conversations_collection.find({"user_id": user_id}).sort(
                "created_at", -1
            )
            conversations = await cursor.to_list(length=None)

            for conv in conversations:
                conv["_id"] = str(conv["_id"])
                if isinstance(conv["user_id"], ObjectId):
                    conv["user_id"] = str(conv["user_id"])

            return conversations
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error finding conversations for user {user_id}: {e}"
            )
            return []

    async def update_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        try:
            conversations = await self._get_collection()
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating conversation title {conversation_id}: {e}"
            )
            return False

    async def update_excluded_ids(
        self, conversation_id: str, excluded_ids: List[str]
    ) -> bool:
        """Update conversation excluded_ids."""
        try:
            print(
                f"🔍 DEBUG update_excluded_ids: Updating conversation {conversation_id}"
            )
            print(f"🔍 DEBUG update_excluded_ids: New excluded_ids: {excluded_ids}")
            conversations = await self._get_collection()
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "excluded_ids": excluded_ids,  # Database field name
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            print(
                f"🔍 DEBUG update_excluded_ids: Update result - matched: {result.matched_count}, modified: {result.modified_count}"
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating conversation excluded_ids {conversation_id}: {e}"
            )
            print(f"🔍 DEBUG update_excluded_ids: Exception: {e}")
            return False

    async def increment_message_count(self, conversation_id: str) -> bool:
        """Increment message count for conversation."""
        from datetime import datetime

        try:
            conversations = await self._get_collection()
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$inc": {"message_count": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error incrementing message count for conversation {conversation_id}: {e}"
            )
            return False
