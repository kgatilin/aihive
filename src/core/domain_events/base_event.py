import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events in the system."""
    
    # Event metadata
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # Will be set by subclasses
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    
    # Context information
    aggregate_id: Optional[str] = None  # ID of the aggregate that generated this event
    correlation_id: Optional[str] = None  # For tracking related events
    causation_id: Optional[str] = None  # ID of event that caused this one
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True  # Events are immutable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create an event instance from a dictionary."""
        return cls(**data) 