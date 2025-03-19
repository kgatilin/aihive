"""
Unit tests for requirement domain events.

These tests verify the functionality of the requirement-related domain events.
"""

import pytest
from datetime import datetime
import uuid
from typing import Dict, Any

from src.core.domain_events.requirement_events import (
    RequirementCreatedEvent,
    RequirementRefinedEvent,
    RequirementStatusChangedEvent,
    RequirementValidatedEvent,
    RequirementMappedToCodeEvent
)


class TestRequirementCreatedEvent:
    """Tests for the RequirementCreatedEvent class."""
    
    def test_initialization(self):
        """Test that RequirementCreatedEvent can be initialized correctly."""
        event = RequirementCreatedEvent(
            requirement_id="req-123",
            title="Test Requirement",
            description="A test requirement",
            priority="high",
            created_by="test_user",
            tags=["test", "requirement"]
        )
        
        assert event.event_type == "requirement.created"
        assert event.requirement_id == "req-123"
        assert event.title == "Test Requirement"
        assert event.description == "A test requirement"
        assert event.priority == "high"
        assert event.created_by == "test_user"
        assert hasattr(event, "status")
        assert event.tags == ["test", "requirement"]
        assert hasattr(event, "acceptance_criteria")
        assert hasattr(event, "related_requirements")
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        event = RequirementCreatedEvent(
            event_id=event_id,
            timestamp=timestamp,
            requirement_id="req-123",
            title="Test Requirement",
            description="A test requirement",
            priority="high",
            created_by="test_user",
            status="draft"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event_id
        assert event_dict["event_type"] == "requirement.created"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["requirement_id"] == "req-123"
        assert event_dict["title"] == "Test Requirement"
        assert event_dict["description"] == "A test requirement"
        assert event_dict["priority"] == "high"
        assert event_dict["created_by"] == "test_user"
        assert event_dict["status"] == "draft"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "requirement_id": "req-123",
            "title": "Test Requirement",
            "description": "A test requirement",
            "priority": "high",
            "created_by": "test_user",
            "status": "draft",
            "tags": ["test", "requirement"],
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "related_requirements": ["req-456"]
        }
        
        event = RequirementCreatedEvent.from_dict(data)
        
        assert event.event_id == event_id
        assert event.timestamp.isoformat() == timestamp.isoformat()
        assert event.requirement_id == "req-123"
        assert event.title == "Test Requirement"
        assert event.description == "A test requirement"
        assert event.priority == "high"
        assert event.created_by == "test_user"
        assert event.status == "draft"
        assert event.tags == ["test", "requirement"]
        assert event.acceptance_criteria == ["Criterion 1", "Criterion 2"]
        assert event.related_requirements == ["req-456"]


class TestRequirementRefinedEvent:
    """Tests for the RequirementRefinedEvent class."""
    
    def test_initialization(self):
        """Test that RequirementRefinedEvent can be initialized correctly."""
        previous_version = {
            "title": "Old Title",
            "description": "Old description"
        }
        
        event = RequirementRefinedEvent(
            requirement_id="req-123",
            previous_version=previous_version,
            updated_fields=["title", "description"],
            refined_by="ai_agent",
            refinement_notes="Improved clarity"
        )
        
        assert event.event_type == "requirement.refined"
        assert event.requirement_id == "req-123"
        assert event.previous_version == previous_version
        assert event.updated_fields == ["title", "description"]
        assert event.refined_by == "ai_agent"
        assert event.refinement_notes == "Improved clarity"
        assert event.refinement_source == "product_agent"  # Default value
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        previous_version = {
            "title": "Old Title",
            "description": "Old description"
        }
        
        event = RequirementRefinedEvent(
            event_id=event_id,
            timestamp=timestamp,
            requirement_id="req-123",
            previous_version=previous_version,
            updated_fields=["title", "description"],
            refined_by="ai_agent",
            refinement_notes="Improved clarity",
            refinement_source="human"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event_id
        assert event_dict["event_type"] == "requirement.refined"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["requirement_id"] == "req-123"
        assert event_dict["previous_version"] == previous_version
        assert event_dict["updated_fields"] == ["title", "description"]
        assert event_dict["refined_by"] == "ai_agent"
        assert event_dict["refinement_notes"] == "Improved clarity"
        assert event_dict["refinement_source"] == "human"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        previous_version = {
            "title": "Old Title",
            "description": "Old description"
        }
        
        data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "requirement_id": "req-123",
            "previous_version": previous_version,
            "updated_fields": ["title", "description"],
            "refined_by": "ai_agent",
            "refinement_notes": "Improved clarity",
            "refinement_source": "human"
        }
        
        event = RequirementRefinedEvent.from_dict(data)
        
        assert event.event_id == event_id
        assert event.timestamp.isoformat() == timestamp.isoformat()
        assert event.requirement_id == "req-123"
        assert event.previous_version == previous_version
        assert event.updated_fields == ["title", "description"]
        assert event.refined_by == "ai_agent"
        assert event.refinement_notes == "Improved clarity"
        assert event.refinement_source == "human"


class TestRequirementStatusChangedEvent:
    """Tests for the RequirementStatusChangedEvent class."""
    
    def test_initialization(self):
        """Test that RequirementStatusChangedEvent can be initialized correctly."""
        event = RequirementStatusChangedEvent(
            requirement_id="req-123",
            previous_status="draft",
            new_status="approved",
            changed_by="product_owner",
            reason="Requirements met"
        )
        
        assert event.event_type == "requirement.status_changed"
        assert event.requirement_id == "req-123"
        assert event.previous_status == "draft"
        assert event.new_status == "approved"
        assert event.changed_by == "product_owner"
        assert event.reason == "Requirements met"
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
    
    def test_optional_reason(self):
        """Test that reason is optional."""
        event = RequirementStatusChangedEvent(
            requirement_id="req-123",
            previous_status="draft",
            new_status="approved",
            changed_by="product_owner"
        )
        
        assert event.reason is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        event = RequirementStatusChangedEvent(
            event_id=event_id,
            timestamp=timestamp,
            requirement_id="req-123",
            previous_status="draft",
            new_status="approved",
            changed_by="product_owner",
            reason="Requirements met"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event_id
        assert event_dict["event_type"] == "requirement.status_changed"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["requirement_id"] == "req-123"
        assert event_dict["previous_status"] == "draft"
        assert event_dict["new_status"] == "approved"
        assert event_dict["changed_by"] == "product_owner"
        assert event_dict["reason"] == "Requirements met"
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "requirement_id": "req-123",
            "previous_status": "draft",
            "new_status": "approved",
            "changed_by": "product_owner",
            "reason": "Requirements met"
        }
        
        event = RequirementStatusChangedEvent.from_dict(data)
        
        assert event.event_id == event_id
        assert event.timestamp.isoformat() == timestamp.isoformat()
        assert event.requirement_id == "req-123"
        assert event.previous_status == "draft"
        assert event.new_status == "approved"
        assert event.changed_by == "product_owner"
        assert event.reason == "Requirements met"


class TestRequirementValidatedEvent:
    """Tests for the RequirementValidatedEvent class."""
    
    def test_initialization(self):
        """Test that RequirementValidatedEvent can be initialized correctly."""
        event = RequirementValidatedEvent(
            requirement_id="req-123",
            validated_by="reviewer",
            validation_status="approved",
            validation_notes="Meets all standards",
            feedback={"clarity": 5, "feasibility": 4}
        )
        
        assert event.event_type == "requirement.validated"
        assert event.requirement_id == "req-123"
        assert event.validated_by == "reviewer"
        assert event.validation_status == "approved"
        assert event.validation_notes == "Meets all standards"
        assert event.feedback == {"clarity": 5, "feasibility": 4}
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
        assert hasattr(event, "validation_timestamp")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        validation_timestamp = datetime.utcnow()
        
        event = RequirementValidatedEvent(
            event_id=event_id,
            timestamp=timestamp,
            requirement_id="req-123",
            validated_by="reviewer",
            validation_timestamp=validation_timestamp,
            validation_status="approved",
            validation_notes="Meets all standards",
            feedback={"clarity": 5, "feasibility": 4}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event_id
        assert event_dict["event_type"] == "requirement.validated"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["requirement_id"] == "req-123"
        assert event_dict["validated_by"] == "reviewer"
        assert event_dict["validation_timestamp"] == validation_timestamp.isoformat()
        assert event_dict["validation_status"] == "approved"
        assert event_dict["validation_notes"] == "Meets all standards"
        assert event_dict["feedback"] == {"clarity": 5, "feasibility": 4}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        validation_timestamp = datetime.utcnow()
        
        data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "requirement_id": "req-123",
            "validated_by": "reviewer",
            "validation_timestamp": validation_timestamp.isoformat(),
            "validation_status": "approved",
            "validation_notes": "Meets all standards",
            "feedback": {"clarity": 5, "feasibility": 4}
        }
        
        event = RequirementValidatedEvent.from_dict(data)
        
        assert event.event_id == event_id
        assert event.timestamp.isoformat() == timestamp.isoformat()
        assert event.requirement_id == "req-123"
        assert event.validated_by == "reviewer"
        assert event.validation_timestamp.isoformat() == validation_timestamp.isoformat()
        assert event.validation_status == "approved"
        assert event.validation_notes == "Meets all standards"
        assert event.feedback == {"clarity": 5, "feasibility": 4}


class TestRequirementMappedToCodeEvent:
    """Tests for the RequirementMappedToCodeEvent class."""
    
    def test_initialization(self):
        """Test that RequirementMappedToCodeEvent can be initialized correctly."""
        event = RequirementMappedToCodeEvent(
            requirement_id="req-123",
            code_artifact_ids=["file1.py", "file2.py"],
            mapped_by="developer",
            mapping_notes="Implementation complete",
            coverage_percentage=95.5
        )
        
        assert event.event_type == "requirement.mapped_to_code"
        assert event.requirement_id == "req-123"
        assert event.code_artifact_ids == ["file1.py", "file2.py"]
        assert event.mapped_by == "developer"
        assert event.mapping_notes == "Implementation complete"
        assert event.coverage_percentage == 95.5
        assert hasattr(event, "event_id")
        assert hasattr(event, "timestamp")
    
    def test_optional_fields(self):
        """Test that some fields are optional."""
        event = RequirementMappedToCodeEvent(
            requirement_id="req-123",
            code_artifact_ids=["file1.py"],
            mapped_by="developer"
        )
        
        assert event.mapping_notes is None
        assert event.coverage_percentage is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        event = RequirementMappedToCodeEvent(
            event_id=event_id,
            timestamp=timestamp,
            requirement_id="req-123",
            code_artifact_ids=["file1.py", "file2.py"],
            mapped_by="developer",
            mapping_notes="Implementation complete",
            coverage_percentage=95.5
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_id"] == event_id
        assert event_dict["event_type"] == "requirement.mapped_to_code"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["requirement_id"] == "req-123"
        assert event_dict["code_artifact_ids"] == ["file1.py", "file2.py"]
        assert event_dict["mapped_by"] == "developer"
        assert event_dict["mapping_notes"] == "Implementation complete"
        assert event_dict["coverage_percentage"] == 95.5
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        data = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat(),
            "requirement_id": "req-123",
            "code_artifact_ids": ["file1.py", "file2.py"],
            "mapped_by": "developer",
            "mapping_notes": "Implementation complete",
            "coverage_percentage": 95.5
        }
        
        event = RequirementMappedToCodeEvent.from_dict(data)
        
        assert event.event_id == event_id
        assert event.timestamp.isoformat() == timestamp.isoformat()
        assert event.requirement_id == "req-123"
        assert event.code_artifact_ids == ["file1.py", "file2.py"]
        assert event.mapped_by == "developer"
        assert event.mapping_notes == "Implementation complete"
        assert event.coverage_percentage == 95.5 