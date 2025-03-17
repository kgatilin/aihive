from typing import ClassVar, List, Optional
from datetime import datetime

from src.core.domain_events.base_event import DomainEvent


class TaskCreatedEvent(DomainEvent):
    """Event emitted when a new task is created."""
    
    event_type: ClassVar[str] = "task.created"
    
    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: str,
        created_by: str,
        requirements_ids: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.created_by = created_by
        self.requirements_ids = requirements_ids or []
        self.parent_task_id = parent_task_id
        self.tags = tags or []
        self.due_date = due_date


class TaskAssignedEvent(DomainEvent):
    """Event emitted when a task is assigned to a user."""
    
    event_type: ClassVar[str] = "task.assigned"
    
    def __init__(
        self,
        task_id: str,
        assignee: str,
        previous_assignee: Optional[str] = None,
        assigned_by: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.assignee = assignee
        self.previous_assignee = previous_assignee
        self.assigned_by = assigned_by


class TaskStatusChangedEvent(DomainEvent):
    """Event emitted when a task's status changes."""
    
    event_type: ClassVar[str] = "task.status_changed"
    
    def __init__(
        self,
        task_id: str,
        new_status: str,
        previous_status: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.new_status = new_status
        self.previous_status = previous_status
        self.changed_by = changed_by
        self.reason = reason


class TaskCompletedEvent(DomainEvent):
    """Event emitted when a task is completed."""
    
    event_type: ClassVar[str] = "task.completed"
    
    def __init__(
        self,
        task_id: str,
        completed_by: str,
        artifact_ids: Optional[List[str]] = None,
        completion_notes: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.completed_by = completed_by
        self.artifact_ids = artifact_ids or []
        self.completion_notes = completion_notes


class TaskCanceledEvent(DomainEvent):
    """Event emitted when a task is canceled."""
    
    event_type: ClassVar[str] = "task.canceled"
    
    def __init__(
        self,
        task_id: str,
        canceled_by: str,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.canceled_by = canceled_by
        self.reason = reason 