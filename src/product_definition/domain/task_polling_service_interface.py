"""
This module defines the interface for the Task Polling Service in the Product Definition domain.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.task_management.domain.entities.task import Task


class TaskPollingServiceInterface(ABC):
    """
    Interface defining the responsibilities of the Task Polling Service.
    The Task Polling Service periodically polls for tasks assigned to agents
    and schedules them for processing based on priority.
    """
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the task polling service.
        This should typically start a background task that runs the polling loop.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the task polling service.
        This should stop the polling loop and perform any necessary cleanup.
        """
        pass
    
    @abstractmethod
    async def poll_tasks(self) -> List[Task]:
        """
        Poll for tasks that are assigned to the agent but not yet processed.
        
        Returns:
            A list of tasks that need to be processed
        """
        pass
    
    @abstractmethod
    async def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Prioritize the list of tasks based on business rules.
        
        Args:
            tasks: The list of tasks to prioritize
            
        Returns:
            The prioritized list of tasks
        """
        pass
    
    @abstractmethod
    async def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest priority task to process.
        
        Returns:
            The next task to process, or None if no tasks are available
        """
        pass
    
    @abstractmethod
    async def mark_task_as_in_progress(self, task: Task) -> Task:
        """
        Mark a task as being in progress to prevent other agents from processing it.
        
        Args:
            task: The task to mark as in progress
            
        Returns:
            The updated task
        """
        pass
    
    @abstractmethod
    async def mark_task_as_completed(self, task: Task) -> Task:
        """
        Mark a task as completed after processing.
        
        Args:
            task: The task to mark as completed
            
        Returns:
            The updated task
        """
        pass 