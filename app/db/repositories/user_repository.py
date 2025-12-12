from typing import Optional, Dict, Any
from .interfaces.base_repo import IBaseRepository
from datetime import datetime, timezone
from bson import ObjectId
from app.db.schemas import User
from app.db.database.base_connection import BaseConnection


class UserRepository(BaseConnection, IBaseRepository):
    """MongoDB implementation of user repository."""

    def __init__(self, db=None):
        super().__init__(db)

    async def _get_collection(self):
        """Get users collection."""
        database = await self.db
        return database["users"]

    # Base Repository Methods
    async def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID."""
        try:
            users = await self._get_collection()
            user = await users.find_one({"_id": ObjectId(entity_id)})
            if user:
                user["_id"] = str(user["_id"])
                return dict(user)
            return None

        except Exception as e:
            self.logger.error(f"[DATABASE] Error finding user by ID {entity_id}: {e}")
            return None

    async def create(self, data: Dict[str, Any]) -> str:
        """Create new user and return ID."""
        try:
            user = User(
                username=data.get("username"),
                email=data.get("email"),
                created_at=datetime.now(timezone.utc),
            )

            users = await self._get_collection()
            result = await users.insert_one(dict(user))
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"[DATABASE] Error creating user: {e}")
            return None

    async def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update user by ID."""
        try:
            users = await self._get_collection()
            result = await users.update_one(
                {"_id": ObjectId(entity_id)}, {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"[DATABASE] Error updating user {entity_id}: {e}")
            return False

    async def delete(self, entity_id: str) -> bool:
        """Delete user by ID."""
        try:
            users = await self._get_collection()
            result = await users.delete_one({"_id": ObjectId(entity_id)})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"[DATABASE] Error deleting user {entity_id}: {e}")
            return False

    # User-specific Methods
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        try:
            users = await self._get_collection()
            user = await users.find_one({"email": email})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            self.logger.error(f"[DATABASE] Error finding user by email {email}: {e}")
            return None

    def find_all(self):
        pass
