"""
Task service for managing tasks.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.task_management.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for managing tasks.
    """
    
    def __init__(self):
        """Initialize the task service."""
        self._tasks = {}  # In-memory storage for demo purposes
    
    def create_task(self, task: Task) -> Task:
        """
        Create a new task.
        
        Args:
            task: The task to create
            
        Returns:
            The created task
        """
        if task.task_id in self._tasks:
            raise ValueError(f"Task with ID {task.task_id} already exists")
        
        self._tasks[task.task_id] = task
        logger.info(f"Created task {task.task_id}: {task.title}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: The ID of the task to get
            
        Returns:
            The task if found, None otherwise
        """
        return self._tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Task]:
        """
        Update a task.
        
        Args:
            task_id: The ID of the task to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated task if found, None otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        logger.info(f"Updated task {task_id}")
        return task
    
    def update_task_status(self, task_id: str, new_status: str, changed_by: str = "system", reason: Optional[str] = None) -> Optional[Task]:
        """
        Update the status of a task.
        
        Args:
            task_id: The ID of the task to update
            new_status: The new status
            changed_by: ID of the user who changed the status
            reason: Reason for the status change
            
        Returns:
            The updated task if found, None otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Update the status
        old_status = task.status
        task.update_status(new_status, changed_by, reason)
        
        logger.info(f"Updated task {task_id} status from {old_status} to {new_status}")
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: The ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Deleted task {task_id}")
            return True
        return False
    
    def add_comment(self, task_id: str, comment: str, created_by: str = "system") -> Optional[Task]:
        """
        Add a comment to a task.
        
        Args:
            task_id: The ID of the task to comment on
            comment: The comment text
            created_by: ID of the user who created the comment
            
        Returns:
            The updated task if found, None otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        task.add_comment(comment, created_by)
        logger.info(f"Added comment to task {task_id}")
        return task
    
    def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Task]:
        """
        List tasks with optional filtering.
        
        Args:
            filters: Optional dictionary of filters to apply
            
        Returns:
            List of tasks matching the filters
        """
        tasks = list(self._tasks.values())
        
        if not filters:
            return tasks
        
        # Apply filters
        filtered_tasks = []
        for task in tasks:
            match = True
            for key, value in filters.items():
                if hasattr(task, key):
                    task_value = getattr(task, key)
                    if task_value != value:
                        match = False
                        break
            
            if match:
                filtered_tasks.append(task)
        
        return filtered_tasks 