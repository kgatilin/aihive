import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.task_management.application.task_service import TaskService
from src.task_management.domain.task import Task, TaskStatus, TaskPriority


class TestTaskService:
    """Test suite for the TaskService."""

    @pytest.mark.asyncio
    async def test_create_task(self, mock_task_repository, mock_message_broker, sample_task_dict):
        """Test creating a new task."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        
        # Configure mocks
        mock_task_repository.save.return_value = None
        mock_message_broker.publish_event.return_value = None
        
        # Act
        task = await service.create_task(
            title=sample_task_dict["title"],
            description=sample_task_dict["description"],
            priority="medium",
            created_by=sample_task_dict["created_by"]
        )
        
        # Assert
        assert task is not None
        assert task.title == sample_task_dict["title"]
        assert task.description == sample_task_dict["description"]
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_by == sample_task_dict["created_by"]
        assert task.status == TaskStatus.CREATED
        
        # Verify interactions with dependencies
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_task(self, mock_task_repository, mock_message_broker, sample_task):
        """Test assigning a task to someone."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        task_id = sample_task.task_id
        
        # Configure mocks
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.save.return_value = None
        mock_message_broker.publish_event.return_value = None
        
        # Act
        task = await service.assign_task(
            task_id=task_id,
            assignee="agent-1",
            assigned_by="admin",
            reason="Test assignment"
        )
        
        # Assert
        assert task is not None
        assert task.assignee == "agent-1"
        assert task.status == TaskStatus.ASSIGNED
        
        # Verify interactions with dependencies
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        # Two events should be published (assignment and status change)
        assert mock_message_broker.publish_event.call_count == 2

    @pytest.mark.asyncio
    async def test_update_task_status(self, mock_task_repository, mock_message_broker, sample_task):
        """Test updating a task's status."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        task_id = sample_task.task_id
        
        # Set initial task state
        sample_task.status = TaskStatus.ASSIGNED
        sample_task.assignee = "agent-1"
        
        # Configure mocks
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.save.return_value = None
        mock_message_broker.publish_event.return_value = None
        
        # Act
        task = await service.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.IN_PROGRESS.value,
            changed_by="agent-1",
            reason="Starting work"
        )
        
        # Assert
        assert task is not None
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Verify interactions with dependencies
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        mock_message_broker.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_task(self, mock_task_repository, mock_message_broker, sample_task):
        """Test marking a task as completed."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        task_id = sample_task.task_id
        
        # Set initial task state
        sample_task.status = TaskStatus.REVIEW
        sample_task.assignee = "agent-1"
        
        # Configure mocks
        mock_task_repository.get_by_id.return_value = sample_task
        mock_task_repository.save.return_value = None
        mock_message_broker.publish_event.return_value = None
        
        # Act
        task = await service.complete_task(
            task_id=task_id,
            completed_by="reviewer",
            outcome_summary="Successfully completed",
            deliverable_ids=["code-1", "code-2"],
            quality_metrics={"score": 95}
        )
        
        # Assert
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        
        # Verify interactions with dependencies
        mock_task_repository.get_by_id.assert_called_once_with(task_id)
        mock_task_repository.save.assert_called_once()
        # Two events should be published (status change and completion)
        assert mock_message_broker.publish_event.call_count == 2

    @pytest.mark.asyncio
    async def test_get_task(self, mock_task_repository, mock_message_broker, sample_task):
        """Test getting a task by ID."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        task_id = sample_task.task_id
        
        # Configure mocks
        mock_task_repository.get_by_id.return_value = sample_task
        
        # Act
        task = await service.get_task(task_id)
        
        # Assert
        assert task is not None
        assert task.task_id == task_id
        
        # Verify interactions with dependencies
        mock_task_repository.get_by_id.assert_called_once_with(task_id)

    @pytest.mark.asyncio
    async def test_find_tasks_by_status(self, mock_task_repository, mock_message_broker, sample_task):
        """Test finding tasks by status."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        status = TaskStatus.IN_PROGRESS.value
        
        # Configure mocks
        mock_task_repository.find_by_status.return_value = [sample_task]
        
        # Act
        tasks = await service.find_tasks_by_status(status)
        
        # Assert
        assert tasks is not None
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify interactions with dependencies
        mock_task_repository.find_by_status.assert_called_once_with(status)

    @pytest.mark.asyncio
    async def test_find_tasks_by_assignee(self, mock_task_repository, mock_message_broker, sample_task):
        """Test finding tasks by assignee."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        assignee = "agent-1"
        
        # Configure mocks
        mock_task_repository.find_by_assignee.return_value = [sample_task]
        
        # Act
        tasks = await service.find_tasks_by_assignee(assignee)
        
        # Assert
        assert tasks is not None
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify interactions with dependencies
        mock_task_repository.find_by_assignee.assert_called_once_with(assignee)

    @pytest.mark.asyncio
    async def test_find_tasks_by_criteria(self, mock_task_repository, mock_message_broker, sample_task):
        """Test finding tasks by criteria."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        criteria = {"tags": "important"}
        
        # Configure mocks
        mock_task_repository.find_by_criteria.return_value = [sample_task]
        
        # Act
        tasks = await service.find_tasks_by_criteria(criteria)
        
        # Assert
        assert tasks is not None
        assert len(tasks) == 1
        assert tasks[0].task_id == sample_task.task_id
        
        # Verify interactions with dependencies
        mock_task_repository.find_by_criteria.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_task_not_found(self, mock_task_repository, mock_message_broker):
        """Test behavior when a task is not found."""
        # Arrange
        service = TaskService(mock_task_repository, mock_message_broker)
        task_id = "non-existent-task"
        
        # Configure mocks
        mock_task_repository.get_by_id.return_value = None
        
        # Act/Assert
        with pytest.raises(ValueError, match=f"Task with ID {task_id} not found"):
            await service.assign_task(task_id, "agent-1", "admin") 