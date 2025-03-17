from enum import Enum

class TaskPriority(str, Enum):
    """Enumeration of possible task priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical" 