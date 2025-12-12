# app/api/repositories/interfaces/__init__.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


# Base Repository Interface
class IBaseRepository(ABC):
    """Base repository interface for common operations."""

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Find entity by ID."""
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> str:
        """Create new entity and return ID."""
        pass

    @abstractmethod
    def update(self, entity_id: str, data: Dict[str, Any]) -> bool:
        """Update entity by ID."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    def find_all(self) -> list[Dict[str, Any]]:
        """Find all entities."""
        pass
