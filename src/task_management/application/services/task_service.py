import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.domain.repositories.task_repository_interface import TaskRepositoryInterface
from src.core.message_broker.message_broker_interface import MessageBroker


logger = logging.getLogger(__name__)


class TaskService:
    """Application service for task management."""
    
    def __init__(self, task_repository: TaskRepositoryInterface, message_broker: MessageBroker):
        """Initialize the task service."""
        self.task_repository = task_repository
        self.message_broker = message_broker
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        created_by: str = "system",
        due_date: Optional[datetime] = None,
        requirements_ids: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """Create a new task."""
        try:
            # Convert string priority to enum
            task_priority = TaskPriority(priority.lower())
            
            # Create the task entity
            task = Task(
                title=title,
                description=description,
                priority=task_priority,
                created_by=created_by,
                due_date=due_date,
                requirements_ids=requirements_ids,
                parent_task_id=parent_task_id,
                tags=tags
            )
            
            # Save to repository
            await self.task_repository.save(task)
            
            # Publish domain events
            for event in task.get_pending_events():
                await self.message_broker.publish_event(event)
            
            # Clear events after publishing
            task.clear_events()
            
            logger.info(f"Created task {task.task_id}")
            return task
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise
    
    async def assign_task(self, task_id: str, assignee: str, assigned_by: Optional[str] = None) -> Task:
        """Assign a task to a user."""
        try:
            # Get the task
            task = await self.task_repository.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # Update the task
            task.assign_to(assignee, assigned_by)
            
            # Save changes
            await self.task_repository.save(task)
            
            # Publish events
            for event in task.get_pending_events():
                await self.message_broker.publish_event(event)
            
            # Clear events
            task.clear_events()
            
            logger.info(f"Assigned task {task_id} to {assignee}")
            return task
        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {str(e)}")
            raise
    
    async def update_task_status(
        self, 
        task_id: str, 
        new_status: str, 
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Task:
        """Update a task's status."""
        try:
            # Get the task
            task = await self.task_repository.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # Update the status
            task.change_status(TaskStatus(new_status), changed_by, reason)
            
            # Save changes
            await self.task_repository.save(task)
            
            # Publish events
            for event in task.get_pending_events():
                await self.message_broker.publish_event(event)
            
            # Clear events
            task.clear_events()
            
            logger.info(f"Updated task {task_id} status to {new_status}")
            return task
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status: {str(e)}")
            raise
    
    async def complete_task(
        self, 
        task_id: str, 
        completed_by: str,
        artifact_ids: Optional[List[str]] = None,
        completion_notes: Optional[str] = None
    ) -> Task:
        """Mark a task as completed."""
        try:
            # Get the task
            task = await self.task_repository.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # Complete the task
            task.complete(completed_by, artifact_ids, completion_notes)
            
            # Save changes
            await self.task_repository.save(task)
            
            # Publish events
            for event in task.get_pending_events():
                await self.message_broker.publish_event(event)
            
            # Clear events
            task.clear_events()
            
            logger.info(f"Completed task {task_id}")
            return task
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        try:
            return await self.task_repository.get_by_id(task_id)
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            raise
    
    async def find_tasks_by_status(self, status: str) -> List[Task]:
        """Find tasks by status."""
        try:
            return await self.task_repository.find_by_status(TaskStatus(status))
        except Exception as e:
            logger.error(f"Failed to find tasks by status {status}: {str(e)}")
            raise
    
    async def find_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """Find tasks by assignee."""
        try:
            return await self.task_repository.find_by_assignee(assignee)
        except Exception as e:
            logger.error(f"Failed to find tasks by assignee {assignee}: {str(e)}")
            raise
    
    async def find_tasks_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find tasks by criteria."""
        try:
            # Convert string status to enum if present
            if "status" in criteria and isinstance(criteria["status"], str):
                criteria["status"] = TaskStatus(criteria["status"])
            
            # Convert string priority to enum if present
            if "priority" in criteria and isinstance(criteria["priority"], str):
                criteria["priority"] = TaskPriority(criteria["priority"])
            
            return await self.task_repository.find_by_criteria(criteria)
        except Exception as e:
            logger.error(f"Failed to find tasks by criteria: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str, canceled_by: str, reason: Optional[str] = None) -> Task:
        """Cancel a task."""
        try:
            # Get the task
            task = await self.task_repository.get_by_id(task_id)
            if not task:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # Cancel the task
            task.cancel(canceled_by, reason)
            
            # Save changes
            await self.task_repository.save(task)
            
            # Publish events
            for event in task.get_pending_events():
                await self.message_broker.publish_event(event)
            
            # Clear events
            task.clear_events()
            
            logger.info(f"Canceled task {task_id}")
            return task
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            raise 