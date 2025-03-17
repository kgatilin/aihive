from enum import Enum

class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELED = "canceled" 