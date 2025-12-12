"""Conversation schema definition."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Conversation(BaseModel):
    """Conversation model for storing conversation metadata."""

    _id: Optional[str] = None
    user_id: str = Field(..., description="ID of the user who owns this conversation")
    created_at: datetime = Field(default_factory=datetime.now)
    message_count: int = Field(default=0, ge=0)
    last_message_at: Optional[datetime] = None
    last_message_timestamp: Optional[datetime] = None
    excluded_ids: List[str] = Field(
        default_factory=list,
        description="List of document IDs to exclude in this conversation",
    )
