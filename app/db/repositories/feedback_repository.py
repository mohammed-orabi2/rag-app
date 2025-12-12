from typing import List, Optional, Dict, Any
from .interfaces.base_repo import IBaseRepository
from bson import ObjectId
from app.db.database.base_connection import BaseConnection


class FeedbackRepository(BaseConnection, IBaseRepository):
    """MongoDB implementation of feedback repository."""

    def __init__(self, db=None):
        super().__init__(db)

    async def _get_collection(self):
        """Get feedback collection."""
        database = await self.db
        return database["feedback"]

    # Base Repository Methods
    async def find_by_id(
        self, entity_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find feedback by ID, optionally filtered by user_id."""

        try:
            query = {"_id": ObjectId(entity_id)}
            if user_id:
                query["user_id"] = user_id

            feedback = await self._get_collection()
            feedback_doc = await feedback.find_one(query)
            if feedback_doc:
                feedback_doc["_id"] = str(feedback_doc["_id"])

                if feedback_doc.get("message_id") and isinstance(
                    feedback_doc["message_id"], ObjectId
                ):
                    feedback_doc["message_id"] = str(feedback_doc["message_id"])
            return feedback_doc
        except Exception as e:
            self.logger.error(f"Error finding feedback by ID {entity_id}: {e}")
            return None

    async def create(
        self,
        conversation_id: str,
        rating: int,
        user_name: str,
        comment: Optional[str] = None,
        message_id: Optional[str] = None,
        langsmith_feedback_id: Optional[str] = None,
        langsmith_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create new feedback with full context."""
        from datetime import datetime

        try:
            feedback_data = {
                "conversation_id": conversation_id,
                "rating": rating,
                "user_name": user_name,
                "comment": comment,
                "timestamp": datetime.utcnow(),
                "langsmith_feedback_id": langsmith_feedback_id,
                "langsmith_run_id": langsmith_run_id,
            }

            if message_id:
                feedback_data["message_id"] = message_id

            feedback = await self._get_collection()
            result = await feedback.insert_one(feedback_data)
            feedback_id = str(result.inserted_id)

            return {
                "success": True,
                "message": "Feedback created successfully",
                "feedback_id": feedback_id,
            }
        except Exception as e:
            self.logger.error(f"Error creating feedback: {e}")
            return {
                "success": False,
                "message": f"Error creating feedback: {str(e)}",
                "feedback_id": None,
            }

    async def update(
        self, entity_id: str, data: Dict[str, Any], user_id: Optional[str] = None
    ) -> bool:
        """Update feedback by ID, optionally filtered by user_id."""
        try:
            query = {"_id": ObjectId(entity_id)}
            if user_id:
                query["user_id"] = user_id

            feedback = await self._get_collection()
            result = await feedback.update_one(query, {"$set": data})
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating feedback {entity_id}: {e}")
            return False

    async def delete(self, entity_id: str) -> bool:
        """Delete feedback by ID."""
        try:
            feedback = await self._get_collection()
            result = await feedback.delete_one({"_id": ObjectId(entity_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting feedback {entity_id}: {e}")
            return False

    async def find_by_conversation_id(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get all feedback for a conversation."""
        try:
            feedback_collection = await self._get_collection()
            cursor = feedback_collection.find(
                {"conversation_id": conversation_id}
            ).sort("timestamp", -1)
            feedbacks = await cursor.to_list(length=None)

            for fb in feedbacks:
                fb["_id"] = str(fb["_id"])
                if fb.get("message_id") and isinstance(fb["message_id"], ObjectId):
                    fb["message_id"] = str(fb["message_id"])

            return feedbacks
        except Exception as e:
            self.logger.error(
                f"Error finding feedback for conversation {conversation_id}: {e}"
            )
            return []

    async def find_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all feedback by user."""
        try:
            feedback_collection = await self._get_collection()
            cursor = (
                feedback_collection.find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            feedbacks = await cursor.to_list(length=None)

            for fb in feedbacks:
                fb["_id"] = str(fb["_id"])
                if fb.get("message_id") and isinstance(fb["message_id"], ObjectId):
                    fb["message_id"] = str(fb["message_id"])

            return feedbacks
        except Exception as e:
            self.logger.error(f"Error finding feedback for user {user_id}: {e}")
            return []

    def find_all():
        pass
