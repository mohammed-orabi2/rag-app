"""Database schema for feedback system."""

from datetime import datetime
from typing import Optional
from bson import ObjectId


class FeedbackSchema:
    """Database schema for feedback collection."""

    @staticmethod
    def create_document(
        user_id: str,
        conversation_id: str,
        rating: int,
        user_name: str,
        comment: Optional[str] = None,
        message_id: Optional[str] = None,
        langsmith_feedback_id: Optional[str] = None,
        langsmith_run_id: Optional[str] = None,
    ) -> dict:
        """Create a feedback document for database storage."""
        return {
            "_id": ObjectId(),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating,
            "comment": comment,
            "user_name": user_name,
            "langsmith_feedback_id": langsmith_feedback_id,
            "langsmith_run_id": langsmith_run_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def to_response_format(document: dict) -> dict:
        """Convert database document to API response format."""
        return {
            "id": str(document["_id"]),
            "user_id": document["user_id"],
            "conversation_id": document["conversation_id"],
            "message_id": document.get("message_id"),
            "rating": document["rating"],
            "comment": document.get("comment"),
            "user_name": document["user_name"],
            "langsmith_feedback_id": document.get("langsmith_feedback_id"),
            "langsmith_run_id": document.get("langsmith_run_id"),
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
        }
