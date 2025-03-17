from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus


class TaskRepositoryInterface(ABC):
    """Interface for task repository implementations."""
    
    @abstractmethod
    async def save(self, task: Task) -> None:
        """Save a task to the repository."""
        pass
    
    @abstractmethod
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Find tasks by status."""
        pass
    
    @abstractmethod
    async def find_by_assignee(self, assignee: str) -> List[Task]:
        """Find tasks by assignee."""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find tasks by arbitrary criteria."""
        pass
    
    @abstractmethod
    async def delete(self, task_id: str) -> bool:
        """Delete a task from the repository."""
        pass
    
    @abstractmethod
    async def find_by_due_date_range(self, start_date: datetime, end_date: datetime) -> List[Task]:
        """Find tasks with due dates in the specified range."""
        pass
    
    @abstractmethod
    async def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Task]:
        """Find tasks by tags.
        
        Args:
            tags: The tags to search for
            match_all: If True, all tags must match. If False, any tag can match.
        """
        pass
    
    @abstractmethod
    async def find_by_parent_task(self, parent_task_id: str) -> List[Task]:
        """Find tasks that are children of the specified parent task."""
        pass 