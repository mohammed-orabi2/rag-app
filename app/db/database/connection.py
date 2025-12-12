"""MongoDB connection management with dependency injection."""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import db_config as config
from utils.logging_info import get_logger

logger = get_logger()


class DatabaseConnectionManager:
    """Database connection manager."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False

    async def connect(self):
        """Connect to MongoDB."""
        if self._is_connected and self.client is not None:
            return

        try:

            self.client = AsyncIOMotorClient(
                config.url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            # Test connection
            await self.client.admin.command("ping")
            self.database = self.client[config.name]
            self._is_connected = True
            logger.info(f"Connected to MongoDB: {config.name}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._is_connected = False
            logger.info("🔌 Database disconnected")

    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected and self.database is not None

    async def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance, connecting if necessary."""
        if not self.is_connected():
            await self.connect()
        return self.database


# Global database manager
db_manager = DatabaseConnectionManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency function for FastAPI."""
    return await db_manager.get_database()


async def close_database_connection():
    """Close the global database connection."""
    global db_manager
    await db_manager.disconnect()
