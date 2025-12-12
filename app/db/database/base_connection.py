from abc import ABC
from .connection import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.logging_info import get_logger


class BaseConnection(ABC):
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db
        self.logger = get_logger()

    async def _ensure_db(self):
        """Ensure database connection is established."""
        if self._db is None:
            self._db = await get_database()
        return self._db

    @property
    async def db(self) -> AsyncIOMotorDatabase:
        """Get database instance asynchronously."""
        return await self._ensure_db()
