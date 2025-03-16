from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import Field

from src.core.domain_events.base_event import DomainEvent


class RequirementCreatedEvent(DomainEvent):
    """Event emitted when a new requirement is created in the system."""
    
    event_type: str = "requirement.created"
    requirement_id: str
    title: str
    description: str
    priority: str
    created_by: str
    status: str = "draft"
    acceptance_criteria: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    related_requirements: List[str] = Field(default_factory=list)


class RequirementRefinedEvent(DomainEvent):
    """Event emitted when a requirement is refined by an agent."""
    
    event_type: str = "requirement.refined"
    requirement_id: str
    previous_version: Dict[str, Any]
    updated_fields: List[str]
    refined_by: str
    refinement_notes: str
    refinement_source: str = "product_agent"  # Could be 'product_agent', 'human', 'automatic'


class RequirementStatusChangedEvent(DomainEvent):
    """Event emitted when a requirement's status changes."""
    
    event_type: str = "requirement.status_changed"
    requirement_id: str
    previous_status: str
    new_status: str
    changed_by: str
    reason: Optional[str] = None


class RequirementValidatedEvent(DomainEvent):
    """Event emitted when a requirement is validated by a human."""
    
    event_type: str = "requirement.validated"
    requirement_id: str
    validated_by: str
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_notes: Optional[str] = None
    validation_status: str  # "approved", "rejected", "needs_revision"
    feedback: Dict[str, Any] = Field(default_factory=dict)


class RequirementMappedToCodeEvent(DomainEvent):
    """Event emitted when a requirement is mapped to implemented code."""
    
    event_type: str = "requirement.mapped_to_code"
    requirement_id: str
    code_artifact_ids: List[str]
    mapped_by: str
    mapping_notes: Optional[str] = None
    coverage_percentage: Optional[float] = None  # How much of the requirement is covered 