from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str
    email: EmailStr


class UserLogin(BaseModel):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = "New Chat"
    email: Optional[EmailStr] = None


class MessageCreate(BaseModel):
    content: str
    role: str = "user"
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    message_count: int
    last_message_at: Optional[datetime]


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    message_type: Optional[str]
    langsmith_run_id: Optional[str] = None
    workflow_metadata: Optional[dict] = None


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class FeedbackRequest(BaseModel):
    """Feedback request schema for creating feedback."""

    email: EmailStr = Field(..., description="User email address")
    conversation_id: str = Field(..., description="ID of the conversation")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, description="Optional feedback comment")
    message_id: Optional[str] = Field(
        None, description="ID of the specific message being rated"
    )
    langsmith_run_id: Optional[str] = Field(
        None, description="LangSmith run ID for tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "conversation_id": "conv_123456",
                "rating": 4,
                "comment": "Very helpful response!",
                "message_id": "msg_789012",
                "langsmith_run_id": "run_345678",
            }
        }


class FeedbackResponse(BaseModel):
    """Feedback submission response."""

    success: bool
    message: str
    feedback_id: str = Field(..., description="ID of the created feedback")
