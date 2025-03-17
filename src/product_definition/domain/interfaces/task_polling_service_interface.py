"""
Interface for the Task Polling Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.task_management.domain.entities.task import Task


class TaskPollingServiceInterface(ABC):
    """
    Interface for the Task Polling Service.
    
    The Task Polling Service is responsible for periodically polling for tasks
    assigned to an agent, prioritizing them, and processing them.
    """
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the polling service.
        
        This method will start a background task that periodically polls for
        tasks assigned to the agent.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the polling service.
        
        This method will stop the background task and perform any necessary cleanup.
        """
        pass
    
    @abstractmethod
    async def poll_tasks(self) -> List[Task]:
        """
        Poll for tasks assigned to the agent.
        
        This method will retrieve all tasks assigned to the agent that are in a
        processable state.
        
        Returns:
            A list of tasks assigned to the agent.
        """
        pass
    
    @abstractmethod
    async def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Prioritize tasks based on their priority and status.
        
        Args:
            tasks: The tasks to prioritize.
            
        Returns:
            The prioritized list of tasks.
        """
        pass
    
    @abstractmethod
    async def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest priority task.
        
        Returns:
            The next task to process, or None if there are no tasks.
        """
        pass
    
    @abstractmethod
    async def mark_task_as_in_progress(self, task: Task) -> Task:
        """
        Mark a task as in progress.
        
        Args:
            task: The task to mark as in progress.
            
        Returns:
            The updated task.
        """
        pass
    
    @abstractmethod
    async def mark_task_as_completed(self, task: Task) -> Task:
        """
        Mark a task as completed.
        
        Args:
            task: The task to mark as completed.
            
        Returns:
            The updated task.
        """
        pass 