from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from src.task_management.domain.task import Task


class TaskRepository(ABC):
    """Repository interface for Task aggregates."""
    
    @abstractmethod
    async def save(self, task: Task) -> None:
        """Save a Task to the repository."""
        pass
    
    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get a Task by its ID."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[Task]:
        """Find Tasks by their status."""
        pass
    
    @abstractmethod
    async def find_by_assignee(self, assignee: str) -> List[Task]:
        """Find Tasks assigned to a specific assignee."""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find Tasks matching the given criteria."""
        pass
    
    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """Delete a Task by its ID. Returns True if successful."""
        pass 