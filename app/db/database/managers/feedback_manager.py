from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.db.schemas.feedback import FeedbackSchema
from utils.logging_info import get_logger
from app.db.repositories.feedback_repository import FeedbackRepository

logger = get_logger()


class FeedbackManager:
    def __init__(self, feedback_collection, conversation_getter):
        self.feedback = feedback_collection
        self.get_conversation = conversation_getter

    def create_feedback(
        self,
        user_id: str,
        conversation_id: str,
        rating: int,
        user_name: str,
        feedback_repo: FeedbackRepository,
        comment: Optional[str] = None,
        message_id: Optional[str] = None,
        langsmith_feedback_id: Optional[str] = None,
        langsmith_run_id: Optional[str] = None,
    ) -> str:
        return feedback_repo.create(
            user_id,
            conversation_id,
            rating,
            user_name,
            comment=comment,
            message_id=message_id,
            langsmith_feedback_id=langsmith_feedback_id,
            langsmith_run_id=langsmith_run_id,
        )

    def get_feedback(
        self, feedback_id: str, user_id: str, feedback_repo: FeedbackRepository
    ) -> Optional[dict]:
        return feedback_repo.find_by_id(feedback_id, user_id)

    def get_conversation_feedback(
        self, conversation_id: str, feedback_repo: FeedbackRepository
    ) -> List[dict]:
        return feedback_repo.find_by_conversation_id(conversation_id)

    def get_user_feedback(
        self, user_id: str, feedback_repo: FeedbackRepository, limit=50
    ) -> List[dict]:
        return feedback_repo.find_by_user_id(user_id, limit)

    def update_feedback_langsmith_id(
        self,
        feedback_id: str,
        user_id: str,
        langsmith_feedback_id: str,
        feedback_repo: FeedbackRepository,
    ) -> bool:
        try:
            update_data = {
                "langsmith_feedback_id": langsmith_feedback_id,
                "updated_at": datetime.utcnow(),
            }

            return feedback_repo.update(feedback_id, update_data, user_id)
        except Exception as e:
            logger.error(f"Error updating feedback LangSmith ID: {e}")
            return False
