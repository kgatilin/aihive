import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.task_management.application.services.task_service import TaskService
from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.domain.events.task_events import (
    TaskCreatedEvent,
    TaskAssignedEvent,
    TaskStatusChangedEvent,
    TaskCompletedEvent
)


@pytest.mark.asyncio
class TestTaskService:
    """Tests for the TaskService."""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.find_by_status = AsyncMock(return_value=[])
        repo.find_by_assignee = AsyncMock(return_value=[])
        repo.find_by_criteria = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_message_broker(self):
        """Create a mock message broker."""
        broker = AsyncMock()
        broker.publish_event = AsyncMock()
        return broker
    
    @pytest.fixture
    def task_service(self, mock_task_repository, mock_message_broker):
        """Create a task service with mocked dependencies."""
        return TaskService(mock_task_repository, mock_message_broker)
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        task = Task(
            task_id="test-123",
            title="Test Task",
            description="This is a test task",
            priority=TaskPriority.MEDIUM,
            created_by="test_user"
        )
        # Clear events to start with a clean slate
        task.clear_events()
        return task
    
    async def test_create_task(self, task_service, mock_task_repository, mock_message_broker):
        """Test creating a task."""
        # Arrange
        title = "New Task"
        description = "This is a new task"
        priority = "medium"
        created_by = "test_user"
        
        # Mock the save method to return None (void)
        mock_task_repository.save.return_value = None
        
        # Act
        task = await task_service.create_task(
            title=title,
            description=description,
            priority=priority,
            created_by=created_by
        )
        
        # Assert
        assert task is not None
        assert task.title == title
        assert task.description == description
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_by == created_by
        
        # Verify repository and broker interactions
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()
        
        # Verify the event published was a TaskCreatedEvent
        published_event = mock_message_broker.publish_event.call_args[0][0]
        assert isinstance(published_event, TaskCreatedEvent)
        assert published_event.task_id == task.task_id
    
    async def test_assign_task(self, task_service, mock_task_repository, mock_message_broker, sample_task):
        """Test assigning a task."""
        # Arrange
        task_id = "test-123"
        assignee = "assignee_user"
        assigned_by = "admin_user"
        
        # Mock repository to return our sample task
        mock_task_repository.get_by_id.return_value = sample_task
        
        # Act
        updated_task = await task_service.assign_task(
            task_id=task_id,
            assignee=assignee,
            assigned_by=assigned_by
        )
        
        # Assert
        assert updated_task.assignee == assignee
        assert updated_task.status == TaskStatus.ASSIGNED
        
        # Verify repository and broker interactions
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()
        
        # Verify the event published was a TaskAssignedEvent
        published_event = mock_message_broker.publish_event.call_args[0][0]
        assert isinstance(published_event, TaskAssignedEvent)
        assert published_event.task_id == task_id
        assert published_event.assignee == assignee
    
    async def test_update_task_status(self, task_service, mock_task_repository, mock_message_broker, sample_task):
        """Test updating a task's status."""
        # Arrange
        task_id = "test-123"
        new_status = "in_progress"
        changed_by = "test_user"
        reason = "Starting work"
        
        # Set the task to ASSIGNED status for a valid transition
        sample_task.status = TaskStatus.ASSIGNED
        sample_task.assignee = "test_user"
        
        # Mock repository to return our sample task
        mock_task_repository.get_by_id.return_value = sample_task
        
        # Act
        updated_task = await task_service.update_task_status(
            task_id=task_id,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        
        # Assert
        assert updated_task.status == TaskStatus.IN_PROGRESS
        
        # Verify repository and broker interactions
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()
        
        # Verify the event published was a TaskStatusChangedEvent
        published_event = mock_message_broker.publish_event.call_args[0][0]
        assert isinstance(published_event, TaskStatusChangedEvent)
        assert published_event.task_id == task_id
        assert published_event.new_status == new_status
        assert published_event.changed_by == changed_by
        assert published_event.reason == reason
    
    async def test_complete_task(self, task_service, mock_task_repository, mock_message_broker, sample_task):
        """Test completing a task."""
        # Arrange
        task_id = "test-123"
        completed_by = "test_user"
        artifact_ids = ["artifact-1", "artifact-2"]
        completion_notes = "Task completed successfully"
        
        # Set the task to REVIEW status for a valid transition to COMPLETED
        sample_task.status = TaskStatus.REVIEW
        
        # Mock repository to return our sample task
        mock_task_repository.get_by_id.return_value = sample_task
        
        # Act
        updated_task = await task_service.complete_task(
            task_id=task_id,
            completed_by=completed_by,
            artifact_ids=artifact_ids,
            completion_notes=completion_notes
        )
        
        # Assert
        assert updated_task.status == TaskStatus.COMPLETED
        assert set(updated_task.artifact_ids) == set(artifact_ids)
        
        # Verify repository and broker interactions
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()
        
        # Verify the event published was a TaskCompletedEvent
        published_event = mock_message_broker.publish_event.call_args[0][0]
        assert isinstance(published_event, TaskCompletedEvent)
        assert published_event.task_id == task_id
        assert published_event.completed_by == completed_by
        assert set(published_event.artifact_ids) == set(artifact_ids)
        assert published_event.completion_notes == completion_notes
    
    async def test_get_task(self, task_service, mock_task_repository, sample_task):
        """Test getting a task by ID."""
        # Arrange
        task_id = "test-123"
        
        # Mock repository to return our sample task
        mock_task_repository.get_by_id.return_value = sample_task
        
        # Act
        task = await task_service.get_task(task_id)
        
        # Assert
        assert task is not None
        assert task.task_id == task_id
        
        # Verify repository interaction
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
    
    async def test_find_tasks_by_status(self, task_service, mock_task_repository, sample_task):
        """Test finding tasks by status."""
        # Arrange
        status = "in_progress"
        
        # Mock repository to return a list with our sample task
        mock_task_repository.find_by_status.return_value = [sample_task]
        
        # Act
        tasks = await task_service.find_tasks_by_status(status)
        
        # Assert
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify repository interaction
        mock_task_repository.find_by_status.assert_called_once()
        # Check that the status was converted to enum
        assert mock_task_repository.find_by_status.call_args[0][0] == TaskStatus.IN_PROGRESS
    
    async def test_find_tasks_by_assignee(self, task_service, mock_task_repository, sample_task):
        """Test finding tasks by assignee."""
        # Arrange
        assignee = "test_user"
        
        # Mock repository to return a list with our sample task
        mock_task_repository.find_by_assignee.return_value = [sample_task]
        
        # Act
        tasks = await task_service.find_tasks_by_assignee(assignee)
        
        # Assert
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify repository interaction
        mock_task_repository.find_by_assignee.assert_called_once_with(assignee)
    
    async def test_find_tasks_by_criteria(self, task_service, mock_task_repository, sample_task):
        """Test finding tasks by criteria."""
        # Arrange
        criteria = {
            "status": "in_progress",
            "priority": "high",
            "tags": ["important"]
        }
        
        # Mock repository to return a list with our sample task
        mock_task_repository.find_by_criteria.return_value = [sample_task]
        
        # Act
        tasks = await task_service.find_tasks_by_criteria(criteria)
        
        # Assert
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify repository interaction
        mock_task_repository.find_by_criteria.assert_called_once()
        # Check that the status and priority were converted to enums
        call_args = mock_task_repository.find_by_criteria.call_args[0][0]
        assert call_args["status"] == TaskStatus.IN_PROGRESS
        assert call_args["priority"] == TaskPriority.HIGH
        assert call_args["tags"] == ["important"]
    
    async def test_task_not_found(self, task_service, mock_task_repository):
        """Test behavior when a task is not found."""
        # Arrange
        task_id = "nonexistent-task"
        
        # Mock repository to return None
        mock_task_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Task with ID {task_id} not found"):
            await task_service.assign_task(
                task_id=task_id,
                assignee="test_user",
                assigned_by="admin"
            ) 