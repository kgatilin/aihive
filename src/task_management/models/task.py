"""
Task model and related enums.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class TaskStatus(Enum):
    """Status of a task."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELED = "canceled"
    ERROR = "error"


class TaskPriority(Enum):
    """Priority of a task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """
    Task entity representing a unit of work in the system.
    """
    
    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        created_by: str,
        status: str = TaskStatus.CREATED.value,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a Task.
        
        Args:
            task_id: Unique identifier for the task
            title: Title of the task
            description: Description of the task
            created_by: ID of the user who created the task
            status: Current status of the task
            priority: Priority of the task
            assignee: ID of the user assigned to the task
            tags: List of tags for the task
            metadata: Additional metadata for the task
            created_at: When the task was created
            updated_at: When the task was last updated
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.created_by = created_by
        self.status = status
        self.priority = priority
        self.assignee = assignee
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.status_history = []
        self.comments = []
    
    def update_status(self, new_status: str, changed_by: str, reason: Optional[str] = None) -> None:
        """
        Update the status of the task.
        
        Args:
            new_status: The new status
            changed_by: ID of the user who changed the status
            reason: Reason for the status change
        """
        self.status = new_status
        self.updated_at = datetime.now()
        
        # Add status change to history
        self.status_history.append({
            'status': new_status,
            'changed_by': changed_by,
            'reason': reason,
            'timestamp': self.updated_at
        })
    
    def add_comment(self, comment: str, created_by: str) -> None:
        """
        Add a comment to the task.
        
        Args:
            comment: The comment text
            created_by: ID of the user who created the comment
        """
        self.comments.append({
            'text': comment,
            'created_by': created_by,
            'timestamp': datetime.now()
        })
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the task.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the task.
        
        Args:
            tag: The tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata item.
        
        Args:
            key: The metadata key
            value: The metadata value
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'status': self.status,
            'priority': self.priority.value,
            'assignee': self.assignee,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 