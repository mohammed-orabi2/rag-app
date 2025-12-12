from typing import Dict, Optional, Any
from app.db.repositories.user_repository import UserRepository


class UserService:
    """Service for user operations."""

    def __init__(self, user_repository: UserRepository = None):
        """Initialize with repository or create a new one if not provided."""
        self.user_repository = user_repository or UserRepository()

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            user_data: Dictionary containing user information

        Returns:
            Dictionary with operation result and user ID
        """
        try:
            user_found = await self.get_user_by_email(user_data.get("email"))
            if user_found.get("success"):
                return {
                    "success": False,
                    "user_id": None,
                    "message": "User already exists",
                }
            user_id = await self.user_repository.create(user_data)

            if user_id:
                # Retrieve the created user to return in the response
                created_user = await self.get_user(user_id)
                return {
                    "success": True,
                    "user_id": user_id,
                    "message": "User created successfully",
                    "user": created_user,
                }
            else:
                return {
                    "success": False,
                    "user_id": None,
                    "message": "Failed to create user",
                }
        except Exception as e:
            return {
                "success": False,
                "user_id": None,
                "message": f"Error creating user: {str(e)}",
            }

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user by their ID.

        Args:
            user_id: ID of the user to retrieve

        Returns:
            Dictionary with success flag and user data
        """
        result = await self.user_repository.find_by_id(user_id)
        if result:
            return {"success": True, "user": result}
        return {"success": False, "message": "User not found"}

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their email.

        Args:
            email: Email of the user to retrieve

        Returns:
            User data or None if not found
        """
        result = await self.user_repository.find_by_email(email)
        if result:
            return {"success": True, "user": result}
        return {"success": False, "message": "User not found"}

    async def update_user(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a user.

        Args:
            user_id: ID of the user to update
            update_data: Data to update in the user

        Returns:
            Dictionary with operation result
        """
        result = await self.user_repository.update(user_id, update_data)

        if result:
            return {"success": True, "message": "User updated successfully"}
        else:
            return {"success": False, "message": "Failed to update user"}

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user.

        Args:
            user_id: ID of the user to delete

        Returns:
            Dictionary with operation result
        """
        result = await self.user_repository.delete(user_id)

        if result:
            return {"success": True, "message": "User deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete user"}

    async def user_exists(self, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            email: Email to check

        Returns:
            True if the user exists, False otherwise
        """
        user = await self.user_repository.find_by_email(email)
        return user is not None
