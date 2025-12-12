"""Message schema definition."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message model for storing individual chat messages."""

    _id: Optional[str] = None
    conversation_id: str = Field(
        ..., description="ID of the conversation this message belongs to"
    )
    role: Literal["user", "assistant"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    langsmith_run_id: Optional[str] = Field(
        None, description="LangSmith run ID for tracing"
    )
    workflow_metadata: Optional[dict] = Field(
        None, description="Workflow execution metadata"
    )
    summary: Optional[str] = Field(
        None, description="Cached summary of the message content"
    )
    rewritten_query: Optional[str] = Field(
        default=None, description="The rewritten query for the conversation"
    )
