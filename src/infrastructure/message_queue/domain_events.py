"""
Domain events used for cross-context communication.

This module defines the events and commands used throughout the application
to enable asynchronous communication between bounded contexts.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid


class EventType(Enum):
    """Enumeration of event types used in the system."""
    # User interaction events
    USER_REQUEST_SUBMITTED = auto()
    CLARIFICATION_PROVIDED = auto()
    HUMAN_VALIDATION_PROVIDED = auto()
    
    # Task management events
    TASK_CREATED = auto()
    TASK_STATUS_CHANGED = auto()
    TASK_ASSIGNED = auto()
    TASK_UNASSIGNED = auto()
    TASK_COMMENT_ADDED = auto()
    
    # Product definition events
    CLARIFICATION_REQUESTED = auto()
    PRODUCT_REQUIREMENT_CREATED = auto()
    PRODUCT_REQUIREMENT_UPDATED = auto()
    HUMAN_VALIDATION_REQUESTED = auto()
    
    # Orchestration events
    TASK_SCAN_INITIATED = auto()
    TASK_SCAN_COMPLETED = auto()


class CommandType(Enum):
    """Enumeration of command types used in the system."""
    # Task management commands
    CREATE_TASK = auto()
    UPDATE_TASK_STATUS = auto()
    ASSIGN_TASK = auto()
    UNASSIGN_TASK = auto()
    ADD_TASK_COMMENT = auto()
    
    # Product definition commands
    CREATE_PRODUCT_REQUIREMENT = auto()
    UPDATE_PRODUCT_REQUIREMENT = auto()
    REQUEST_CLARIFICATION = auto()
    LINK_REQUIREMENT_TO_TASK = auto()
    
    # Human interaction commands
    SEND_MESSAGE = auto()
    SEND_NOTIFICATION = auto()


class TaskStatus(Enum):
    """Task states throughout the workflow."""
    NEW = "new"
    REQUEST_VALIDATION = "request_validation"
    CLARIFICATION_NEEDED = "clarification_needed"
    PRD_DEVELOPMENT = "prd_development"
    PRD_VALIDATION = "prd_validation"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Event Data Classes
@dataclass
class EventMetadata:
    """Metadata for domain events."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    version: str = "1.0"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    metadata: EventMetadata
    payload: Dict[str, Any]


# Command Data Classes
@dataclass
class CommandMetadata:
    """Metadata for domain commands."""
    command_id: str
    command_type: CommandType
    timestamp: datetime
    source: str
    version: str = "1.0"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None


@dataclass
class DomainCommand:
    """Base class for all domain commands."""
    metadata: CommandMetadata
    payload: Dict[str, Any]


# Event Factory Functions
def create_event(event_type: EventType, payload: Dict[str, Any], 
                 source: str, correlation_id: Optional[str] = None, 
                 causation_id: Optional[str] = None) -> DomainEvent:
    """
    Create a domain event with the given type and payload.
    
    Args:
        event_type: Type of the event
        payload: Event data
        source: Source component generating the event
        correlation_id: Optional ID to correlate related events
        causation_id: Optional ID of the event that caused this event
    
    Returns:
        A DomainEvent instance
    """
    metadata = EventMetadata(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(),
        source=source,
        correlation_id=correlation_id,
        causation_id=causation_id
    )
    
    return DomainEvent(metadata=metadata, payload=payload)


def create_command(command_type: CommandType, payload: Dict[str, Any], 
                   source: str, correlation_id: Optional[str] = None, 
                   causation_id: Optional[str] = None) -> DomainCommand:
    """
    Create a domain command with the given type and payload.
    
    Args:
        command_type: Type of the command
        payload: Command data
        source: Source component generating the command
        correlation_id: Optional ID to correlate related commands
        causation_id: Optional ID of the event that caused this command
    
    Returns:
        A DomainCommand instance
    """
    metadata = CommandMetadata(
        command_id=str(uuid.uuid4()),
        command_type=command_type,
        timestamp=datetime.now(),
        source=source,
        correlation_id=correlation_id,
        causation_id=causation_id
    )
    
    return DomainCommand(metadata=metadata, payload=payload)


# Serialization / Deserialization Helper Functions
def serialize_event(event: DomainEvent) -> Dict[str, Any]:
    """Convert a DomainEvent to a serializable dictionary."""
    return {
        "metadata": {
            "event_id": event.metadata.event_id,
            "event_type": event.metadata.event_type.name,
            "timestamp": event.metadata.timestamp.isoformat(),
            "source": event.metadata.source,
            "version": event.metadata.version,
            "correlation_id": event.metadata.correlation_id,
            "causation_id": event.metadata.causation_id
        },
        "payload": event.payload
    }


def deserialize_event(data: Dict[str, Any]) -> DomainEvent:
    """Convert a dictionary to a DomainEvent instance."""
    metadata = EventMetadata(
        event_id=data["metadata"]["event_id"],
        event_type=EventType[data["metadata"]["event_type"]],
        timestamp=datetime.fromisoformat(data["metadata"]["timestamp"]),
        source=data["metadata"]["source"],
        version=data["metadata"]["version"],
        correlation_id=data["metadata"]["correlation_id"],
        causation_id=data["metadata"]["causation_id"]
    )
    
    return DomainEvent(metadata=metadata, payload=data["payload"])


def serialize_command(command: DomainCommand) -> Dict[str, Any]:
    """Convert a DomainCommand to a serializable dictionary."""
    return {
        "metadata": {
            "command_id": command.metadata.command_id,
            "command_type": command.metadata.command_type.name,
            "timestamp": command.metadata.timestamp.isoformat(),
            "source": command.metadata.source,
            "version": command.metadata.version,
            "correlation_id": command.metadata.correlation_id,
            "causation_id": command.metadata.causation_id
        },
        "payload": command.payload
    }


def deserialize_command(data: Dict[str, Any]) -> DomainCommand:
    """Convert a dictionary to a DomainCommand instance."""
    metadata = CommandMetadata(
        command_id=data["metadata"]["command_id"],
        command_type=CommandType[data["metadata"]["command_type"]],
        timestamp=datetime.fromisoformat(data["metadata"]["timestamp"]),
        source=data["metadata"]["source"],
        version=data["metadata"]["version"],
        correlation_id=data["metadata"]["correlation_id"],
        causation_id=data["metadata"]["causation_id"]
    )
    
    return DomainCommand(metadata=metadata, payload=data["payload"]) 