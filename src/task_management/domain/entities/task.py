import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.domain.events.task_events import (
    TaskCreatedEvent,
    TaskAssignedEvent,
    TaskStatusChangedEvent,
    TaskCompletedEvent,
    TaskCanceledEvent
)


class Task:
    """Task entity represents a unit of work in the system."""
    
    def __init__(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        created_by: str = "system",
        task_id: Optional[str] = None,
        status: TaskStatus = TaskStatus.CREATED,
        assignee: Optional[str] = None,
        due_date: Optional[datetime] = None,
        requirements_ids: Optional[List[str]] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        artifact_ids: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Core attributes
        self.task_id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status
        self.created_by = created_by
        self.assignee = assignee
        self.due_date = due_date
        self.requirements_ids = requirements_ids or []
        self.parent_task_id = parent_task_id
        self.tags = tags or []
        
        # Timestamps
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        
        # Artifact information
        self.artifact_ids = artifact_ids or []
        
        # Pending domain events
        self._pending_events: List[Any] = []
        
        # Record creation event
        if not task_id:  # Only emit created event if this is a new task
            self._record_created_event()
    
    def assign_to(self, assignee: str, assigned_by: Optional[str] = None) -> None:
        """Assign the task to a user."""
        previous_assignee = self.assignee
        self.assignee = assignee
        
        # Change status if it's in CREATED state
        if self.status == TaskStatus.CREATED:
            self._change_status(TaskStatus.ASSIGNED)
        
        self.updated_at = datetime.utcnow()
        
        # Record the event
        self._pending_events.append(
            TaskAssignedEvent(
                task_id=self.task_id,
                assignee=assignee,
                previous_assignee=previous_assignee,
                assigned_by=assigned_by
            )
        )
    
    def change_status(self, new_status: TaskStatus, changed_by: Optional[str] = None, reason: Optional[str] = None) -> None:
        """Change the task status."""
        if not self._is_valid_status_transition(new_status):
            raise ValueError(f"Invalid status transition from {self.status.value} to {new_status.value}")
        
        previous_status = self.status
        self._change_status(new_status, changed_by, reason)
    
    def complete(self, completed_by: str, artifact_ids: Optional[List[str]] = None, completion_notes: Optional[str] = None) -> None:
        """Mark the task as completed."""
        if self.status == TaskStatus.CANCELED:
            raise ValueError("Cannot complete a canceled task")
        
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.utcnow()
        
        if artifact_ids:
            self.artifact_ids.extend(artifact_ids)
        
        # Record the event
        self._pending_events.append(
            TaskCompletedEvent(
                task_id=self.task_id,
                completed_by=completed_by,
                artifact_ids=self.artifact_ids,
                completion_notes=completion_notes
            )
        )
    
    def cancel(self, canceled_by: str, reason: Optional[str] = None) -> None:
        """Cancel the task."""
        if self.status == TaskStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed task")
        
        self.status = TaskStatus.CANCELED
        self.updated_at = datetime.utcnow()
        
        # Record the event
        self._pending_events.append(
            TaskCanceledEvent(
                task_id=self.task_id,
                canceled_by=canceled_by,
                reason=reason
            )
        )
    
    def start_progress(self, started_by: str) -> None:
        """Start progress on the task."""
        if self.status not in [TaskStatus.ASSIGNED, TaskStatus.BLOCKED]:
            raise ValueError(f"Cannot start progress from status {self.status.value}")
        
        self._change_status(TaskStatus.IN_PROGRESS, started_by)
    
    def block(self, blocked_by: str, reason: str) -> None:
        """Block the task with a reason."""
        if self.status not in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot block task in {self.status.value} status")
        
        self._change_status(TaskStatus.BLOCKED, blocked_by, reason)
    
    def ready_for_review(self, submitted_by: str, artifact_ids: List[str]) -> None:
        """Mark the task as ready for review with artifact IDs."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot submit for review from status {self.status.value}")
        
        self.artifact_ids.extend(artifact_ids)
        self._change_status(TaskStatus.REVIEW, submitted_by)
    
    def get_pending_events(self) -> List[Any]:
        """Get all pending domain events."""
        return list(self._pending_events)
    
    def clear_events(self) -> None:
        """Clear all pending domain events."""
        self._pending_events.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_by": self.created_by,
            "assignee": self.assignee,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "requirements_ids": self.requirements_ids,
            "parent_task_id": self.parent_task_id,
            "tags": self.tags,
            "artifact_ids": self.artifact_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a task from a dictionary."""
        # Convert string values to enums
        if "priority" in data and isinstance(data["priority"], str):
            data["priority"] = TaskPriority(data["priority"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = TaskStatus(data["status"])
        
        # Convert ISO datetime strings to datetime objects
        for date_field in ["due_date", "created_at", "updated_at"]:
            if date_field in data and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        # Create the task instance
        task = cls(**data)
        
        # Don't emit created event for reconstructed tasks
        task._pending_events.clear()
        
        return task
    
    def _record_created_event(self) -> None:
        """Record a task created event."""
        self._pending_events.append(
            TaskCreatedEvent(
                task_id=self.task_id,
                title=self.title,
                description=self.description,
                priority=self.priority.value,
                created_by=self.created_by,
                requirements_ids=self.requirements_ids,
                parent_task_id=self.parent_task_id,
                tags=self.tags,
                due_date=self.due_date
            )
        )
    
    def _change_status(self, new_status: TaskStatus, changed_by: Optional[str] = None, reason: Optional[str] = None) -> None:
        """Change status and record the event."""
        previous_status = self.status
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # Record the event
        self._pending_events.append(
            TaskStatusChangedEvent(
                task_id=self.task_id,
                new_status=new_status.value,
                previous_status=previous_status.value,
                changed_by=changed_by,
                reason=reason
            )
        )
    
    def _is_valid_status_transition(self, new_status: TaskStatus) -> bool:
        """Check if a status transition is valid."""
        # Define valid transitions
        valid_transitions = {
            TaskStatus.CREATED: [TaskStatus.ASSIGNED, TaskStatus.CANCELED],
            TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELED],
            TaskStatus.IN_PROGRESS: [TaskStatus.BLOCKED, TaskStatus.REVIEW, TaskStatus.CANCELED],
            TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELED],
            TaskStatus.REVIEW: [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELED],
            TaskStatus.COMPLETED: [],  # No transitions from completed
            TaskStatus.CANCELED: []    # No transitions from canceled
        }
        
        return new_status in valid_transitions.get(self.status, []) 