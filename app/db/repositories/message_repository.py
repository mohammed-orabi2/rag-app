from typing import List, Optional, Dict, Any
from .interfaces.base_repo import IBaseRepository
from bson import ObjectId
from app.db.schemas import Message
from datetime import datetime, timezone
from app.db.database.base_connection import BaseConnection


class MessageRepository(BaseConnection, IBaseRepository):
    """MongoDB implementation of message repository."""

    def __init__(self, db=None):
        super().__init__(db)

    async def _get_collection(self):
        """Get messages collection."""
        database = await self.db
        return database["messages"]

    # Base Repository Methods
    async def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find message by ID."""
        try:
            messages = await self._get_collection()
            message = await messages.find_one({"_id": ObjectId(entity_id)})
            if message:
                return message
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error finding message by ID {entity_id}: {e}"
            )
            return None

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new message and return ID."""
        try:
            message = Message(
                conversation_id=str(data["conversation_id"]),
                role=data["role"],
                content=data["content"],
                timestamp=datetime.now(timezone.utc),
                # langsmith_run_id=data.get("langsmith_run_id"),
                # workflow_metadata=data.get("workflow_metadata"),
                summary=data.get("summary"),
                rewritten_query=data.get("rewritten_query"),
            )
            messages = await self._get_collection()
            result = await messages.insert_one(dict(message))
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"[DATABASE] Error creating message: {e}")
            return None

    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update message by ID."""
        try:
            messages = await self._get_collection()
            result = await messages.update_one(
                {"_id": ObjectId(entity_id)}, {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"[DATABASE] Error updating message {entity_id}: {e}")
            return False

    async def delete(self, entity_id: str) -> bool:
        """Delete message by ID."""
        try:
            messages = await self._get_collection()
            result = await messages.delete_one({"_id": ObjectId(entity_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"[DATABASE] Error deleting message {entity_id}: {e}")
            return False

    # Message-specific Methods
    async def find_all(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        try:
            messages_collection = await self._get_collection()
            cursor = messages_collection.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", 1)
            messages = await cursor.to_list(length=None)

            for msg in messages:
                msg["_id"] = str(msg["_id"])
                if isinstance(msg["conversation_id"], ObjectId):
                    msg["conversation_id"] = str(msg["conversation_id"])
            return messages
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error finding messages for conversation {conversation_id}: {e}"
            )
            return []

    async def update_content(self, message_id: str, content: str) -> bool:
        """Update message content."""
        try:
            messages = await self._get_collection()
            result = await messages.update_one(
                {"_id": ObjectId(message_id)}, {"$set": {"content": content}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating message content {message_id}: {e}"
            )
            return False

    async def update_summary(self, message_id: str, summary: str) -> bool:
        """Update message summary."""
        try:
            messages = await self._get_collection()
            result = await messages.update_one(
                {"_id": ObjectId(message_id)}, {"$set": {"summary": summary}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating message summary {message_id}: {e}"
            )
            return False

    async def update_rewritten_query(
        self, message_id: str, rewritten_query: str
    ) -> bool:
        """Update message rewritten query."""
        try:
            messages = await self._get_collection()
            result = await messages.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": {"rewritten_query": rewritten_query}},
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error updating message rewritten query {message_id}: {e}"
            )
            return False

    async def count_messages(self, conversation_id: str) -> int:
        try:
            messages = await self._get_collection()
            return await messages.count_documents({"conversation_id": conversation_id})
        except Exception as e:
            self.logger.error(
                f"[DATABASE] Error counting messages for conversation {conversation_id}: {e}"
            )
            return 0
