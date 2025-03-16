import pytest
from datetime import datetime
from unittest.mock import patch

from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.core.domain_events.task_events import (
    TaskAssignedEvent,
    TaskStatusChangedEvent,
    TaskCompletedEvent,
    TaskCanceledEvent
)


class TestTask:
    """Test suite for the Task domain entity."""

    def test_create_task(self):
        """Test creating a new task with default values."""
        # Act
        task = Task(
            title="Test Task",
            description="Test Description",
            created_by="test-user"
        )

        # Assert
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.created_by == "test-user"
        assert task.status == TaskStatus.CREATED
        assert task.priority == TaskPriority.MEDIUM
        assert task.assignee is None
        assert task.requirements_ids == []
        assert task.parent_task_id is None
        assert task.tags == []
        assert task.task_id is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_create_task_with_custom_values(self):
        """Test creating a task with custom values."""
        # Arrange
        task_id = "test-123"
        creation_date = datetime(2023, 1, 1, 12, 0, 0)
        update_date = datetime(2023, 1, 1, 12, 0, 0)

        # Act
        task = Task(
            task_id=task_id,
            title="Custom Task",
            description="Custom Description",
            priority=TaskPriority.HIGH,
            status=TaskStatus.ASSIGNED,
            created_by="admin",
            assignee="agent-1",
            due_date=datetime(2023, 2, 1),
            requirements_ids=["req-1", "req-2"],
            parent_task_id="parent-1",
            tags=["important", "urgent"],
            created_at=creation_date,
            updated_at=update_date
        )

        # Assert
        assert task.task_id == task_id
        assert task.title == "Custom Task"
        assert task.description == "Custom Description"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.ASSIGNED
        assert task.created_by == "admin"
        assert task.assignee == "agent-1"
        assert task.due_date == datetime(2023, 2, 1)
        assert task.requirements_ids == ["req-1", "req-2"]
        assert task.parent_task_id == "parent-1"
        assert task.tags == ["important", "urgent"]
        assert task.created_at == creation_date
        assert task.updated_at == update_date

    def test_assign_to(self):
        """Test assigning a task to someone."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.CREATED,
            created_by="test-user"
        )

        # Act
        task.assign_to("agent-1", "admin", "Testing assignment")

        # Assert
        assert task.assignee == "agent-1"
        assert task.status == TaskStatus.ASSIGNED
        events = task.get_pending_events()
        assert len(events) == 2  # Should have both assignment and status change events
        
        # Verify assignment event
        assignment_event = next((e for e in events if isinstance(e, TaskAssignedEvent)), None)
        assert assignment_event is not None
        assert assignment_event.task_id == "test-123"
        assert assignment_event.previous_assignee is None
        assert assignment_event.new_assignee == "agent-1"
        assert assignment_event.assigned_by == "admin"
        assert assignment_event.assignment_reason == "Testing assignment"

    def test_change_status(self):
        """Test changing a task's status."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.ASSIGNED,
            assignee="agent-1",
            created_by="test-user"
        )

        # Act
        task.change_status(TaskStatus.IN_PROGRESS, "agent-1", "Starting work")

        # Assert
        assert task.status == TaskStatus.IN_PROGRESS
        events = task.get_pending_events()
        assert len(events) == 1
        
        # Verify status change event
        status_event = events[0]
        assert isinstance(status_event, TaskStatusChangedEvent)
        assert status_event.task_id == "test-123"
        assert status_event.previous_status == TaskStatus.ASSIGNED.value
        assert status_event.new_status == TaskStatus.IN_PROGRESS.value
        assert status_event.changed_by == "agent-1"
        assert status_event.reason == "Starting work"

    def test_invalid_status_transition(self):
        """Test that invalid status transitions raise exceptions."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.CREATED,
            created_by="test-user"
        )

        # Act/Assert
        with pytest.raises(ValueError, match=r"Invalid status transition"):
            task.change_status(TaskStatus.IN_PROGRESS, "user", "Invalid transition")

    def test_complete_task(self):
        """Test marking a task as completed."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.REVIEW,
            created_by="test-user"
        )

        # Act
        task.complete("reviewer", "Task successfully completed", 
                     deliverable_ids=["deliverable-1"], 
                     quality_metrics={"score": 95})

        # Assert
        assert task.status == TaskStatus.COMPLETED
        events = task.get_pending_events()
        assert len(events) == 2  # Status change and completion events
        
        # Find the completion event
        completion_event = next((e for e in events if isinstance(e, TaskCompletedEvent)), None)
        assert completion_event is not None
        assert completion_event.task_id == "test-123"
        assert completion_event.completed_by == "reviewer"
        assert completion_event.outcome_summary == "Task successfully completed"
        assert completion_event.deliverable_ids == ["deliverable-1"]
        assert completion_event.quality_metrics == {"score": 95}

    def test_cancel_task(self):
        """Test canceling a task."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.IN_PROGRESS,
            created_by="test-user"
        )

        # Act
        task.cancel("admin", "No longer needed")

        # Assert
        assert task.status == TaskStatus.CANCELED
        events = task.get_pending_events()
        assert len(events) == 2  # Status change and cancellation events
        
        # Find the cancellation event
        cancel_event = next((e for e in events if isinstance(e, TaskCanceledEvent)), None)
        assert cancel_event is not None
        assert cancel_event.task_id == "test-123"
        assert cancel_event.canceled_by == "admin"
        assert cancel_event.reason == "No longer needed"

    def test_cannot_cancel_completed_task(self):
        """Test that completed tasks cannot be canceled."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.COMPLETED,
            created_by="test-user"
        )

        # Act/Assert
        with pytest.raises(ValueError, match=r"Cannot cancel a completed task"):
            task.cancel("admin", "Trying to cancel")

    def test_start_progress(self):
        """Test starting progress on a task."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.ASSIGNED,
            assignee="agent-1",
            created_by="test-user"
        )

        # Act
        task.start_progress("agent-1")

        # Assert
        assert task.status == TaskStatus.IN_PROGRESS

    def test_block_task(self):
        """Test blocking a task."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.IN_PROGRESS,
            assignee="agent-1",
            created_by="test-user"
        )

        # Act
        task.block("agent-1", "Waiting for dependency")

        # Assert
        assert task.status == TaskStatus.BLOCKED

    def test_ready_for_review(self):
        """Test marking a task as ready for review."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.IN_PROGRESS,
            assignee="agent-1",
            created_by="test-user"
        )

        # Act
        task.ready_for_review("agent-1", ["artifact-1"])

        # Assert
        assert task.status == TaskStatus.REVIEW
        
        # Verify event details
        events = task.get_pending_events()
        assert len(events) == 1
        assert events[0].related_artifact_ids == ["artifact-1"]

    def test_clear_events(self):
        """Test clearing pending events."""
        # Arrange
        task = Task(
            task_id="test-123",
            title="Test Task",
            status=TaskStatus.CREATED,
            created_by="test-user"
        )
        task.assign_to("agent-1", "admin")  # This will generate events

        # Act
        events_before = task.get_pending_events()
        task.clear_events()
        events_after = task.get_pending_events()

        # Assert
        assert len(events_before) > 0
        assert len(events_after) == 0 