from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import Field

from src.core.domain_events.base_event import DomainEvent


class TaskCreatedEvent(DomainEvent):
    """Event emitted when a new task is created in the system."""
    
    event_type: str = "task.created"
    task_id: str
    title: str
    description: str
    priority: str
    created_by: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    requirements_ids: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TaskAssignedEvent(DomainEvent):
    """Event emitted when a task is assigned to an agent or person."""
    
    event_type: str = "task.assigned"
    task_id: str
    previous_assignee: Optional[str] = None
    new_assignee: str
    assigned_by: str
    assignment_reason: Optional[str] = None


class TaskStatusChangedEvent(DomainEvent):
    """Event emitted when a task's status changes."""
    
    event_type: str = "task.status_changed"
    task_id: str
    previous_status: str
    new_status: str
    changed_by: str
    reason: Optional[str] = None
    related_artifact_ids: List[str] = Field(default_factory=list)


class TaskCompletedEvent(DomainEvent):
    """Event emitted when a task is marked as completed."""
    
    event_type: str = "task.completed"
    task_id: str
    completed_by: str
    completion_time: datetime = Field(default_factory=datetime.utcnow)
    outcome_summary: str
    deliverable_ids: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)


class TaskCanceledEvent(DomainEvent):
    """Event emitted when a task is canceled."""
    
    event_type: str = "task.canceled"
    task_id: str
    canceled_by: str
    reason: str 