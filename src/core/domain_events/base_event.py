import uuid
from abc import ABC
from datetime import datetime
from typing import Dict, Any, ClassVar, Optional


class DomainEvent(ABC):
    """Base class for all domain events in the system."""
    
    event_type: ClassVar[str] = "domain.event"  # Default event type, should be overridden by subclasses
    version: ClassVar[str] = "1.0"  # Event version for schema evolution
    
    def __init__(
        self,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow()
        # Store additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }
        
        # Add all other attributes except private ones and standard methods
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in data:
                # Handle datetime objects
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                else:
                    data[key] = value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """Create an event instance from a dictionary."""
        # Handle the timestamp specially
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Convert any other datetime strings
        for key, value in data.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass  # Not a valid datetime string, leave as is
        
        # Create an instance with the data
        return cls(**data) 