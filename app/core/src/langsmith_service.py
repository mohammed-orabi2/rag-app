"""LangSmith client service for feedback management."""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from langsmith import Client
from app.config import langsmith_config as config


class LangSmithService:
    """Service for managing LangSmith feedback operations."""

    def __init__(self):
        self.client = None
        self.project_name = config.project

        if config.api_key:
            try:
                # Set environment variables for LangSmith
                os.environ["LANGCHAIN_API_KEY"] = config.api_key
                os.environ["LANGCHAIN_PROJECT"] = config.project
                os.environ["LANGCHAIN_TRACING_V2"] = config.tracing

                self.client = Client(
                    api_key=config.api_key,
                )
            except Exception as e:
                print(f"Failed to initialize LangSmith client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if LangSmith client is available and configured."""
        return self.client is not None

    def create_feedback(
        self,
        run_id: str,
        rating: int,
        comment: Optional[str] = None,
        user_name: str = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Create feedback in LangSmith.

        Args:
            run_id: The LangSmith run ID to associate feedback with
            rating: Rating from 1-5
            comment: Optional feedback comment
            user_name: Name of the user providing feedback
            metadata: Additional metadata to store

        Returns:
            Feedback ID if successful, None otherwise
        """
        if not self.is_available():
            print("LangSmith client not available")
            return None

        try:
            # Validate rating
            if not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5")

            # Prepare metadata
            feedback_metadata = metadata or {}
            if user_name:
                feedback_metadata["user_name"] = user_name

            feedback_metadata["timestamp"] = datetime.utcnow().isoformat()

            # Create feedback in LangSmith
            feedback = self.client.create_feedback(
                run_id=run_id,
                key="user_rating",
                score=rating / 5.0,  # Normalize to 0-1 scale for LangSmith
                value=rating,  # Keep original 1-5 scale as value
                comment=comment,
                metadata=feedback_metadata,
            )

            return feedback.id if feedback else None

        except Exception as e:
            print(f"Error creating LangSmith feedback: {e}")
            return None

    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve feedback from LangSmith.

        Args:
            feedback_id: The feedback ID to retrieve

        Returns:
            Feedback data if found, None otherwise
        """
        if not self.is_available():
            return None

        try:
            feedback = self.client.read_feedback(feedback_id)
            return {
                "id": feedback.id,
                "run_id": feedback.run_id,
                "key": feedback.key,
                "score": feedback.score,
                "value": feedback.value,
                "comment": feedback.comment,
                "metadata": feedback.metadata,
                "created_at": feedback.created_at,
                "modified_at": feedback.modified_at,
            }
        except Exception as e:
            print(f"Error retrieving LangSmith feedback: {e}")
            return None

    def list_feedback_for_run(self, run_id: str) -> list:
        """
        List all feedback for a specific run.

        Args:
            run_id: The run ID to get feedback for

        Returns:
            List of feedback records
        """
        if not self.is_available():
            return []

        try:
            feedback_list = list(self.client.list_feedback(run_ids=[run_id]))
            return [
                {
                    "id": feedback.id,
                    "run_id": feedback.run_id,
                    "key": feedback.key,
                    "score": feedback.score,
                    "value": feedback.value,
                    "comment": feedback.comment,
                    "metadata": feedback.metadata,
                    "created_at": feedback.created_at,
                    "modified_at": feedback.modified_at,
                }
                for feedback in feedback_list
            ]
        except Exception as e:
            print(f"Error listing LangSmith feedback: {e}")
            return []


# Global service instance
langsmith_service = LangSmithService()
