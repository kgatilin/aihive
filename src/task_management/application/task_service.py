import logging
from typing import Optional, List, Dict, Any

from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.task_management.domain.task_repository import TaskRepository
from src.core.domain_events.task_events import TaskCreatedEvent


logger = logging.getLogger(__name__)


class TaskService:
    """Application service for task management operations."""
    
    def __init__(self, task_repository: TaskRepository, message_broker: MessageBroker):
        self.task_repository = task_repository
        self.message_broker = message_broker
    
    async def create_task(
        self,
        title: str,
        description: str,
        priority: str,
        created_by: str,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
        requirements_ids: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """Create a new task."""
        # Create the task domain entity
        task = Task(
            title=title,
            description=description,
            priority=priority,
            created_by=created_by,
            assignee=assignee,
            due_date=due_date,
            requirements_ids=requirements_ids or [],
            parent_task_id=parent_task_id,
            tags=tags or []
        )
        
        # Save the task to the repository
        await self.task_repository.save(task)
        
        # Create TaskCreatedEvent
        created_event = TaskCreatedEvent(
            aggregate_id=task.task_id,
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            priority=task.priority.value,
            created_by=task.created_by,
            assignee=task.assignee,
            due_date=task.due_date,
            requirements_ids=task.requirements_ids,
            parent_task_id=task.parent_task_id,
            tags=task.tags
        )
        
        # Publish the event
        await self.message_broker.publish_event(created_event)
        
        logger.info(f"Created task {task.task_id}: {task.title}")
        return task
    
    async def assign_task(self, task_id: str, assignee: str, assigned_by: str, reason: Optional[str] = None) -> Task:
        """Assign a task to someone."""
        # Fetch the task
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Apply domain operation
        task.assign_to(assignee, assigned_by, reason)
        
        # Save the updated task
        await self.task_repository.save(task)
        
        # Publish all pending events
        for event in task.get_pending_events():
            await self.message_broker.publish_event(event)
        
        # Clear events after publishing
        task.clear_events()
        
        logger.info(f"Task {task_id} assigned to {assignee}")
        return task
    
    async def update_task_status(
        self, 
        task_id: str, 
        new_status: str,
        changed_by: str,
        reason: Optional[str] = None,
        related_artifact_ids: Optional[List[str]] = None
    ) -> Task:
        """Update a task's status."""
        # Fetch the task
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Apply domain operation
        task.change_status(new_status, changed_by, reason, related_artifact_ids)
        
        # Save the updated task
        await self.task_repository.save(task)
        
        # Publish all pending events
        for event in task.get_pending_events():
            await self.message_broker.publish_event(event)
        
        # Clear events after publishing
        task.clear_events()
        
        logger.info(f"Task {task_id} status changed to {new_status}")
        return task
    
    async def complete_task(
        self, 
        task_id: str, 
        completed_by: str, 
        outcome_summary: str,
        deliverable_ids: Optional[List[str]] = None,
        quality_metrics: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Mark a task as completed."""
        # Fetch the task
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Apply domain operation
        task.complete(completed_by, outcome_summary, deliverable_ids, quality_metrics)
        
        # Save the updated task
        await self.task_repository.save(task)
        
        # Publish all pending events
        for event in task.get_pending_events():
            await self.message_broker.publish_event(event)
        
        # Clear events after publishing
        task.clear_events()
        
        logger.info(f"Task {task_id} marked as completed")
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        return await self.task_repository.get_by_id(task_id)
    
    async def find_tasks_by_status(self, status: str) -> List[Task]:
        """Find tasks by their status."""
        return await self.task_repository.find_by_status(status)
    
    async def find_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """Find tasks assigned to someone."""
        return await self.task_repository.find_by_assignee(assignee)
    
    async def find_tasks_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find tasks matching specific criteria."""
        return await self.task_repository.find_by_criteria(criteria) 