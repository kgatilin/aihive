import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.domain.events.task_events import (
    TaskCreatedEvent,
    TaskAssignedEvent,
    TaskStatusChangedEvent,
    TaskCompletedEvent,
    TaskCanceledEvent
)


class TestTask:
    """Tests for the Task entity."""
    
    def test_create_task(self):
        """Test creating a task with default values."""
        # Arrange & Act
        task = Task(
            title="Test Task",
            description="This is a test task"
        )
        
        # Assert
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.CREATED
        assert task.created_by == "system"
        assert task.assignee is None
        assert task.due_date is None
        assert task.requirements_ids == []
        assert task.parent_task_id is None
        assert task.tags == []
        assert task.artifact_ids == []
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.created_at == task.updated_at
        
        # Check that a TaskCreatedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCreatedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].title == task.title
        assert events[0].description == task.description
        assert events[0].priority == task.priority.value
    
    def test_create_task_with_custom_values(self):
        """Test creating a task with custom values."""
        # Arrange
        due_date = datetime.utcnow() + timedelta(days=7)
        
        # Act
        task = Task(
            title="Custom Task",
            description="This is a custom task",
            priority=TaskPriority.HIGH,
            created_by="test_user",
            task_id="test-123",
            status=TaskStatus.ASSIGNED,
            assignee="assignee_user",
            due_date=due_date,
            requirements_ids=["req-1", "req-2"],
            parent_task_id="parent-123",
            tags=["tag1", "tag2"]
        )
        
        # Assert
        assert task.task_id == "test-123"
        assert task.title == "Custom Task"
        assert task.description == "This is a custom task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.ASSIGNED
        assert task.created_by == "test_user"
        assert task.assignee == "assignee_user"
        assert task.due_date == due_date
        assert task.requirements_ids == ["req-1", "req-2"]
        assert task.parent_task_id == "parent-123"
        assert task.tags == ["tag1", "tag2"]
    
    def test_assign_to(self):
        """Test assigning a task to a user."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task"
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.assign_to("test_user", "admin")
        
        # Assert
        assert task.assignee == "test_user"
        assert task.status == TaskStatus.ASSIGNED
        
        # Check that a TaskAssignedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskAssignedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].assignee == "test_user"
        assert events[0].previous_assignee is None
        assert events[0].assigned_by == "admin"
    
    def test_change_status(self):
        """Test changing a task's status."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.ASSIGNED,
            assignee="test_user"
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.change_status(TaskStatus.IN_PROGRESS, "test_user", "Starting work")
        
        # Assert
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Check that a TaskStatusChangedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskStatusChangedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].new_status == TaskStatus.IN_PROGRESS.value
        assert events[0].previous_status == TaskStatus.ASSIGNED.value
        assert events[0].changed_by == "test_user"
        assert events[0].reason == "Starting work"
    
    def test_invalid_status_transition(self):
        """Test that invalid status transitions raise exceptions."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.CREATED
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid status transition"):
            task.change_status(TaskStatus.REVIEW)
    
    def test_complete_task(self):
        """Test completing a task."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.REVIEW
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.complete("test_user", ["artifact-1", "artifact-2"], "Completed successfully")
        
        # Assert
        assert task.status == TaskStatus.COMPLETED
        assert task.artifact_ids == ["artifact-1", "artifact-2"]
        
        # Check that a TaskCompletedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCompletedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].completed_by == "test_user"
        assert events[0].artifact_ids == ["artifact-1", "artifact-2"]
        assert events[0].completion_notes == "Completed successfully"
    
    def test_cancel_task(self):
        """Test canceling a task."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.IN_PROGRESS
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.cancel("test_user", "No longer needed")
        
        # Assert
        assert task.status == TaskStatus.CANCELED
        
        # Check that a TaskCanceledEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskCanceledEvent)
        assert events[0].task_id == task.task_id
        assert events[0].canceled_by == "test_user"
        assert events[0].reason == "No longer needed"
    
    def test_cannot_cancel_completed_task(self):
        """Test that completed tasks cannot be canceled."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.COMPLETED
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot cancel a completed task"):
            task.cancel("test_user")
    
    def test_start_progress(self):
        """Test starting progress on a task."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.ASSIGNED,
            assignee="test_user"
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.start_progress("test_user")
        
        # Assert
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Check that a TaskStatusChangedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskStatusChangedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].new_status == TaskStatus.IN_PROGRESS.value
        assert events[0].previous_status == TaskStatus.ASSIGNED.value
    
    def test_block_task(self):
        """Test blocking a task."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.IN_PROGRESS,
            assignee="test_user"
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.block("test_user", "Waiting for dependency")
        
        # Assert
        assert task.status == TaskStatus.BLOCKED
        
        # Check that a TaskStatusChangedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskStatusChangedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].new_status == TaskStatus.BLOCKED.value
        assert events[0].previous_status == TaskStatus.IN_PROGRESS.value
        assert events[0].reason == "Waiting for dependency"
    
    def test_ready_for_review(self):
        """Test marking a task as ready for review."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task",
            status=TaskStatus.IN_PROGRESS,
            assignee="test_user"
        )
        task.clear_events()  # Clear the creation event
        
        # Act
        task.ready_for_review("test_user", ["artifact-1"])
        
        # Assert
        assert task.status == TaskStatus.REVIEW
        assert task.artifact_ids == ["artifact-1"]
        
        # Check that a TaskStatusChangedEvent was generated
        events = task.get_pending_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskStatusChangedEvent)
        assert events[0].task_id == task.task_id
        assert events[0].new_status == TaskStatus.REVIEW.value
        assert events[0].previous_status == TaskStatus.IN_PROGRESS.value
    
    def test_clear_events(self):
        """Test clearing pending events."""
        # Arrange
        task = Task(
            title="Test Task",
            description="This is a test task"
        )
        assert len(task.get_pending_events()) > 0
        
        # Act
        task.clear_events()
        
        # Assert
        assert len(task.get_pending_events()) == 0
    
    def test_to_dict(self):
        """Test converting a task to a dictionary."""
        # Arrange
        due_date = datetime.utcnow()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        task = Task(
            title="Test Task",
            description="This is a test task",
            priority=TaskPriority.HIGH,
            created_by="test_user",
            task_id="test-123",
            status=TaskStatus.ASSIGNED,
            assignee="assignee_user",
            due_date=due_date,
            requirements_ids=["req-1"],
            parent_task_id="parent-123",
            tags=["tag1"],
            created_at=created_at,
            updated_at=updated_at
        )
        task.artifact_ids = ["artifact-1"]
        
        # Act
        task_dict = task.to_dict()
        
        # Assert
        assert task_dict["task_id"] == "test-123"
        assert task_dict["title"] == "Test Task"
        assert task_dict["description"] == "This is a test task"
        assert task_dict["priority"] == "high"
        assert task_dict["status"] == "assigned"
        assert task_dict["created_by"] == "test_user"
        assert task_dict["assignee"] == "assignee_user"
        assert task_dict["due_date"] == due_date.isoformat()
        assert task_dict["requirements_ids"] == ["req-1"]
        assert task_dict["parent_task_id"] == "parent-123"
        assert task_dict["tags"] == ["tag1"]
        assert task_dict["artifact_ids"] == ["artifact-1"]
        assert task_dict["created_at"] == created_at.isoformat()
        assert task_dict["updated_at"] == updated_at.isoformat()
    
    def test_from_dict(self):
        """Test creating a task from a dictionary."""
        # Arrange
        due_date = datetime.utcnow()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        
        task_dict = {
            "task_id": "test-123",
            "title": "Test Task",
            "description": "This is a test task",
            "priority": "high",
            "status": "assigned",
            "created_by": "test_user",
            "assignee": "assignee_user",
            "due_date": due_date.isoformat(),
            "requirements_ids": ["req-1"],
            "parent_task_id": "parent-123",
            "tags": ["tag1"],
            "artifact_ids": ["artifact-1"],
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat()
        }
        
        # Act
        task = Task.from_dict(task_dict)
        
        # Assert
        assert task.task_id == "test-123"
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.ASSIGNED
        assert task.created_by == "test_user"
        assert task.assignee == "assignee_user"
        assert task.due_date.isoformat() == due_date.isoformat()  # Compare ISO strings due to potential microsecond differences
        assert task.requirements_ids == ["req-1"]
        assert task.parent_task_id == "parent-123"
        assert task.tags == ["tag1"]
        assert task.created_at.isoformat() == created_at.isoformat()
        assert task.updated_at.isoformat() == updated_at.isoformat()
        
        # Check that no events were generated for a reconstructed task
        assert len(task.get_pending_events()) == 0 