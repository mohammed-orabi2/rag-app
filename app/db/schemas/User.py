"""User schema definition."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """User model for storing user information."""

    _id: Optional[str] = None
    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.now)
