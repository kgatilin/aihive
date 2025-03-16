import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from src.core.domain_events.task_events import (
    TaskCreatedEvent,
    TaskAssignedEvent,
    TaskStatusChangedEvent,
    TaskCompletedEvent,
    TaskCanceledEvent
)


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TaskPriority(str, Enum):
    """Enumeration of possible task priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """Task domain entity representing a unit of work in the system."""
    
    def __init__(
        self,
        task_id: Optional[str] = None,
        title: str = "",
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.CREATED,
        created_by: str = "",
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
        requirements_ids: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        # Core attributes
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        
        # Ownership and assignment
        self.created_by = created_by
        self.assignee = assignee
        
        # Timing
        self.due_date = due_date
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Relationships
        self.requirements_ids = requirements_ids or []
        self.parent_task_id = parent_task_id
        self.tags = tags or []
        
        # State tracking
        self._events = []  # Track domain events for this aggregate
    
    def assign_to(self, new_assignee: str, assigned_by: str, reason: Optional[str] = None) -> None:
        """Assign this task to a person or agent."""
        previous_assignee = self.assignee
        self.assignee = new_assignee
        self.updated_at = datetime.utcnow()
        
        # Record the event
        event = TaskAssignedEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            previous_assignee=previous_assignee,
            new_assignee=new_assignee,
            assigned_by=assigned_by,
            assignment_reason=reason
        )
        self._events.append(event)
        
        # If task was in CREATED status, move it to ASSIGNED
        if self.status == TaskStatus.CREATED:
            self.change_status(TaskStatus.ASSIGNED, assigned_by, f"Assigned to {new_assignee}")
    
    def change_status(self, new_status: TaskStatus, changed_by: str, 
                      reason: Optional[str] = None, 
                      related_artifact_ids: Optional[List[str]] = None) -> None:
        """Change the status of this task."""
        if new_status == self.status:
            return  # No change needed
        
        # Validate state transition
        valid = self._is_valid_status_transition(new_status)
        if not valid:
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        previous_status = self.status
        self.status = new_status if isinstance(new_status, TaskStatus) else TaskStatus(new_status)
        self.updated_at = datetime.utcnow()
        
        # Record the event
        event = TaskStatusChangedEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            previous_status=previous_status.value,
            new_status=new_status.value,
            changed_by=changed_by,
            reason=reason,
            related_artifact_ids=related_artifact_ids or []
        )
        self._events.append(event)
    
    def complete(self, completed_by: str, outcome_summary: str, 
                deliverable_ids: Optional[List[str]] = None,
                quality_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Mark this task as completed."""
        if self.status == TaskStatus.COMPLETED:
            return  # Already completed
        
        previous_status = self.status
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.utcnow()
        
        # Record status change event
        status_event = TaskStatusChangedEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            previous_status=previous_status.value,
            new_status=TaskStatus.COMPLETED.value,
            changed_by=completed_by,
            reason=f"Task completed: {outcome_summary[:50]}..."
        )
        self._events.append(status_event)
        
        # Record completion event with details
        completion_event = TaskCompletedEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            completed_by=completed_by,
            outcome_summary=outcome_summary,
            deliverable_ids=deliverable_ids or [],
            quality_metrics=quality_metrics or {}
        )
        self._events.append(completion_event)
    
    def cancel(self, canceled_by: str, reason: str) -> None:
        """Cancel this task."""
        if self.status == TaskStatus.CANCELED:
            return  # Already canceled
        
        # Cannot cancel a completed task
        if self.status == TaskStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed task")
        
        previous_status = self.status
        self.status = TaskStatus.CANCELED
        self.updated_at = datetime.utcnow()
        
        # Record status change event
        status_event = TaskStatusChangedEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            previous_status=previous_status.value,
            new_status=TaskStatus.CANCELED.value,
            changed_by=canceled_by,
            reason=f"Task canceled: {reason[:50]}..."
        )
        self._events.append(status_event)
        
        # Record cancellation event
        cancel_event = TaskCanceledEvent(
            aggregate_id=self.task_id,
            task_id=self.task_id,
            canceled_by=canceled_by,
            reason=reason
        )
        self._events.append(cancel_event)
    
    def start_progress(self, started_by: str) -> None:
        """Start working on this task."""
        if self.status not in [TaskStatus.ASSIGNED, TaskStatus.BLOCKED]:
            raise ValueError(f"Cannot start progress on task in {self.status} status")
        
        self.change_status(TaskStatus.IN_PROGRESS, started_by, "Work started on task")
    
    def block(self, blocked_by: str, reason: str) -> None:
        """Mark this task as blocked."""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELED]:
            raise ValueError(f"Cannot block task in {self.status} status")
        
        self.change_status(TaskStatus.BLOCKED, blocked_by, f"Task blocked: {reason}")
    
    def ready_for_review(self, submitted_by: str, artifact_ids: Optional[List[str]] = None) -> None:
        """Mark this task as ready for review."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot submit for review a task in {self.status} status")
        
        self.change_status(TaskStatus.REVIEW, submitted_by, "Task ready for review", artifact_ids)
    
    def get_pending_events(self) -> List:
        """Get all pending domain events for this aggregate."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all pending domain events after they have been dispatched."""
        self._events.clear()
    
    def _is_valid_status_transition(self, new_status: TaskStatus) -> bool:
        """Check if the status transition is valid according to the workflow rules."""
        # Define allowed transitions
        allowed_transitions = {
            TaskStatus.CREATED: [TaskStatus.ASSIGNED, TaskStatus.CANCELED],
            TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELED],
            TaskStatus.IN_PROGRESS: [TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.CANCELED],
            TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELED],
            TaskStatus.REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELED],
            TaskStatus.COMPLETED: [],  # Terminal state
            TaskStatus.CANCELED: []  # Terminal state
        }
        
        return new_status in allowed_transitions.get(self.status, []) 