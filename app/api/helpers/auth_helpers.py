from fastapi import HTTPException, status, Query
from pydantic import EmailStr
from typing import Optional
from app.api.services.user_services import UserService


async def get_current_user(email: Optional[EmailStr] = Query(None)):
    """Get current user from email parameter"""
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email parameter required for authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_service = UserService()
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
