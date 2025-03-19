"""
Unit tests for the task service in the services package.

These tests verify that the TaskService in src.task_management.services.task_service
works correctly.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.task_management.services.task_service import TaskService
from src.task_management.models.task import Task, TaskStatus


class TestTaskService:
    """Tests for the TaskService."""
    
    @pytest.fixture
    def task_service(self):
        """Create a task service instance."""
        return TaskService()
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            task_id="test-task-1",
            title="Test Task",
            description="This is a test task",
            status="open",
            priority="medium",
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_create_task(self, task_service, sample_task):
        """Test creating a task."""
        result = task_service.create_task(sample_task)
        
        assert result == sample_task
        assert task_service.get_task(sample_task.task_id) == sample_task
    
    def test_create_task_already_exists(self, task_service, sample_task):
        """Test creating a task when it already exists."""
        # First create
        task_service.create_task(sample_task)
        
        # Second create should raise an error
        with pytest.raises(ValueError, match=f"Task with ID {sample_task.task_id} already exists"):
            task_service.create_task(sample_task)
    
    def test_get_task(self, task_service, sample_task):
        """Test getting a task by ID."""
        task_service.create_task(sample_task)
        
        result = task_service.get_task(sample_task.task_id)
        
        assert result == sample_task
    
    def test_get_task_not_found(self, task_service):
        """Test getting a task that doesn't exist."""
        result = task_service.get_task("non-existent-task")
        
        assert result is None
    
    def test_update_task(self, task_service, sample_task):
        """Test updating a task."""
        task_service.create_task(sample_task)
        
        updates = {
            "title": "Updated Title",
            "description": "Updated Description",
            "priority": "high"
        }
        
        with patch('src.task_management.services.task_service.datetime') as mock_datetime:
            mock_now = datetime.now()
            mock_datetime.now.return_value = mock_now
            
            result = task_service.update_task(sample_task.task_id, updates)
        
        assert result is not None
        assert result.title == "Updated Title"
        assert result.description == "Updated Description"
        assert result.priority == "high"
        assert result.updated_at == mock_now
    
    def test_update_task_not_found(self, task_service):
        """Test updating a task that doesn't exist."""
        result = task_service.update_task("non-existent-task", {"title": "New Title"})
        
        assert result is None
    
    def test_update_task_status(self, task_service, sample_task):
        """Test updating a task's status."""
        task_service.create_task(sample_task)
        
        result = task_service.update_task_status(
            task_id=sample_task.task_id,
            new_status="in_progress",
            changed_by="admin",
            reason="Starting work"
        )
        
        assert result is not None
        assert result.status == "in_progress"
    
    def test_update_task_status_not_found(self, task_service):
        """Test updating status of a task that doesn't exist."""
        result = task_service.update_task_status("non-existent-task", "in_progress")
        
        assert result is None
    
    def test_delete_task(self, task_service, sample_task):
        """Test deleting a task."""
        task_service.create_task(sample_task)
        
        result = task_service.delete_task(sample_task.task_id)
        
        assert result is True
        assert task_service.get_task(sample_task.task_id) is None
    
    def test_delete_task_not_found(self, task_service):
        """Test deleting a task that doesn't exist."""
        result = task_service.delete_task("non-existent-task")
        
        assert result is False
    
    def test_add_comment(self, task_service, sample_task):
        """Test adding a comment to a task."""
        # Set up mock for Task's add_comment method
        sample_task.add_comment = MagicMock()
        task_service.create_task(sample_task)
        
        result = task_service.add_comment(
            task_id=sample_task.task_id,
            comment="This is a comment",
            created_by="commenter"
        )
        
        assert result == sample_task
        sample_task.add_comment.assert_called_once_with("This is a comment", "commenter")
    
    def test_add_comment_not_found(self, task_service):
        """Test adding a comment to a task that doesn't exist."""
        result = task_service.add_comment("non-existent-task", "This is a comment")
        
        assert result is None
    
    def test_list_tasks_no_filters(self, task_service, sample_task):
        """Test listing all tasks without filters."""
        task_service.create_task(sample_task)
        
        # Create another task
        another_task = Task(
            task_id="test-task-2",
            title="Another Task",
            description="This is another test task",
            status="in_progress",
            priority="high",
            created_by="another_user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        task_service.create_task(another_task)
        
        result = task_service.list_tasks()
        
        assert len(result) == 2
        assert sample_task in result
        assert another_task in result
    
    def test_list_tasks_with_filters(self, task_service, sample_task):
        """Test listing tasks with filters."""
        task_service.create_task(sample_task)
        
        # Create another task
        another_task = Task(
            task_id="test-task-2",
            title="Another Task",
            description="This is another test task",
            status="in_progress",
            priority="high",
            created_by="another_user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        task_service.create_task(another_task)
        
        # Filter by status
        result = task_service.list_tasks({"status": "open"})
        
        assert len(result) == 1
        assert sample_task in result
        assert another_task not in result
        
        # Filter by created_by
        result = task_service.list_tasks({"created_by": "another_user"})
        
        assert len(result) == 1
        assert sample_task not in result
        assert another_task in result
        
        # Filter with multiple criteria
        result = task_service.list_tasks({
            "status": "in_progress",
            "priority": "high"
        })
        
        assert len(result) == 1
        assert sample_task not in result
        assert another_task in result
        
        # Filter with non-matching criteria
        result = task_service.list_tasks({
            "status": "completed"
        })
        
        assert len(result) == 0 