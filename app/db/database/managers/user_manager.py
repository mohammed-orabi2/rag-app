from typing import Optional
from app.db.repositories.user_repository import UserRepository
from datetime import datetime, timezone


class UserManager(UserRepository):
    """User Manager for handling user-related operations."""

    def create_user(self, username: str, email: str, user_repo: UserRepository) -> dict:
        """Create a new user with business logic."""
        try:
            # Check if user already exists
            existing_user = user_repo.find_by_email(email)
            if existing_user:
                return {
                    "success": True,
                    "user_id": str(existing_user["_id"]),
                    "user": existing_user,
                    "message": "User already exists",
                }

            # Create new user using base repository create method
            user_data = {
                "username": username,
                "email": email,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            user_id = user_repo.create(user_data)
            if user_id:
                # Get the created user
                new_user = user_repo.find_by_id(user_id)
                return {
                    "success": True,
                    "user_id": user_id,
                    "user": new_user,
                    "message": "User created successfully",
                }

            return {
                "success": False,
                "user_id": None,
                "user": None,
                "message": "Failed to create user",
            }
        except Exception as e:
            return {
                "success": False,
                "user_id": None,
                "user": None,
                "message": f"Error creating user: {str(e)}",
            }

    def get_user_by_email(
        self, email: str, user_repo: UserRepository
    ) -> Optional[dict]:
        """Get user by email."""
        return user_repo.find_by_email(email)

    def login_user(self, email: str, user_repo: UserRepository) -> dict:
        """Handle user login with business logic."""
        user = user_repo.find_by_email(email)
        if user:
            return {"success": True, "user": user, "message": "Login successful"}
        return {"success": False, "user": None, "message": "Invalid email"}

    def get_all_users(self, user_repo: UserRepository) -> list:
        """Get all users."""
        return user_repo.get_all_users()
