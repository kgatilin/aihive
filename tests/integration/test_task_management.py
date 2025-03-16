import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.task_management.infrastructure.mongo_task_repository import MongoTaskRepository
from src.task_management.application.task_service import TaskService
from src.task_management.domain.task_repository import TaskRepository


# For integration tests, we'll use an in-memory repository implementation
class InMemoryTaskRepository(TaskRepository):
    """In-memory implementation of the TaskRepository for tests."""
    
    def __init__(self):
        self.tasks = {}
        
    async def connect(self):
        """No connection needed for in-memory repository."""
        pass
        
    async def disconnect(self):
        """No disconnection needed for in-memory repository."""
        pass
        
    async def save(self, task: Task) -> None:
        """Save a task to the in-memory store."""
        self.tasks[task.task_id] = task
        
    async def get_by_id(self, task_id: str) -> Task:
        """Get a task by its ID."""
        return self.tasks.get(task_id)
        
    async def find_by_status(self, status: str) -> list[Task]:
        """Find tasks by status."""
        return [task for task in self.tasks.values() if task.status.value == status]
        
    async def find_by_assignee(self, assignee: str) -> list[Task]:
        """Find tasks by assignee."""
        return [task for task in self.tasks.values() if task.assignee == assignee]
        
    async def find_by_criteria(self, criteria: dict) -> list[Task]:
        """Find tasks by criteria."""
        # Simple implementation for basic criteria
        results = list(self.tasks.values())
        
        if 'tags' in criteria:
            tag = criteria['tags']
            results = [task for task in results if tag in task.tags]
            
        return results
        
    async def delete(self, task_id: str) -> bool:
        """Delete a task by its ID."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


@pytest_asyncio.fixture
async def task_repository():
    """Create an in-memory task repository for testing."""
    repository = InMemoryTaskRepository()
    return repository


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker for testing."""
    broker = AsyncMock(spec=MessageBroker)
    broker.publish_event = AsyncMock()
    broker.subscribe_to_event = AsyncMock()
    broker.publish_command = AsyncMock()
    broker.subscribe_to_command = AsyncMock()
    return broker


@pytest_asyncio.fixture
async def task_service(task_repository, mock_message_broker):
    """Create a task service with in-memory repository and mock message broker."""
    service = TaskService(task_repository, mock_message_broker)
    return service


class TestTaskManagementIntegration:
    """Integration tests for task management components."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_task(self, task_service):
        """Test creating a task and retrieving it."""
        # Arrange
        title = "Integration Test Task"
        description = "Testing task creation and retrieval"
        
        # Act - Create a task
        created_task = await task_service.create_task(
            title=title,
            description=description,
            priority=TaskPriority.HIGH.value,
            created_by="integration-test"
        )
        
        # Act - Retrieve the task
        retrieved_task = await task_service.get_task(created_task.task_id)
        
        # Assert
        assert retrieved_task is not None
        assert retrieved_task.task_id == created_task.task_id
        assert retrieved_task.title == title
        assert retrieved_task.description == description
        assert retrieved_task.priority == TaskPriority.HIGH
        assert retrieved_task.status == TaskStatus.CREATED
        assert retrieved_task.created_by == "integration-test"

    @pytest.mark.asyncio
    async def test_task_lifecycle(self, task_service):
        """Test a complete task lifecycle from creation to completion."""
        # Arrange - Create a task
        task = await task_service.create_task(
            title="Lifecycle Test Task",
            description="Testing the complete task lifecycle",
            priority=TaskPriority.MEDIUM.value,
            created_by="integration-test"
        )
        task_id = task.task_id
        
        # Act 1 - Assign the task
        task = await task_service.assign_task(
            task_id=task_id,
            assignee="test-agent",
            assigned_by="integration-test",
            reason="Testing assignment"
        )
        
        # Assert 1
        assert task.assignee == "test-agent"
        assert task.status == TaskStatus.ASSIGNED
        
        # Act 2 - Start progress on the task
        task = await task_service.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.IN_PROGRESS,  # Pass enum directly instead of string value
            changed_by="test-agent",
            reason="Starting work"
        )
        
        # Assert 2
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Act 3 - Submit for review
        task = await task_service.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.REVIEW,  # Pass enum directly instead of string value
            changed_by="test-agent",
            reason="Ready for review",
            related_artifact_ids=["test-artifact-1"]
        )
        
        # Assert 3
        assert task.status == TaskStatus.REVIEW
        
        # Act 4 - Complete the task
        task = await task_service.complete_task(
            task_id=task_id,
            completed_by="test-reviewer",
            outcome_summary="Task completed successfully",
            deliverable_ids=["test-deliverable-1"],
            quality_metrics={"score": 90}
        )
        
        # Assert 4
        assert task.status == TaskStatus.COMPLETED
        
        # Verify the final state
        final_task = await task_service.get_task(task_id)
        assert final_task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_find_tasks_by_status(self, task_service):
        """Test finding tasks by status."""
        # Arrange - Create multiple tasks with different statuses
        task1 = await task_service.create_task(
            title="Task 1",
            description="First test task",
            priority=TaskPriority.MEDIUM.value,
            created_by="integration-test"
        )
        
        task2 = await task_service.create_task(
            title="Task 2",
            description="Second test task",
            priority=TaskPriority.HIGH.value,
            created_by="integration-test"
        )
        
        # Update task2 status
        await task_service.update_task_status(
            task_id=task2.task_id,
            new_status=TaskStatus.ASSIGNED,  # Pass enum directly
            changed_by="integration-test",
            reason="Testing status search"
        )
        
        # Act - Find tasks by status
        created_tasks = await task_service.find_tasks_by_status(TaskStatus.CREATED.value)
        assigned_tasks = await task_service.find_tasks_by_status(TaskStatus.ASSIGNED.value)
        
        # Assert
        assert len(created_tasks) == 1
        assert created_tasks[0].task_id == task1.task_id
        
        assert len(assigned_tasks) == 1
        assert assigned_tasks[0].task_id == task2.task_id

    @pytest.mark.asyncio
    async def test_find_tasks_by_assignee(self, task_service):
        """Test finding tasks by assignee."""
        # Arrange - Create and assign tasks
        task1 = await task_service.create_task(
            title="Assignee Task 1",
            description="First assignee test task",
            priority=TaskPriority.MEDIUM.value,
            created_by="integration-test"
        )
        
        task2 = await task_service.create_task(
            title="Assignee Task 2",
            description="Second assignee test task",
            priority=TaskPriority.HIGH.value,
            created_by="integration-test"
        )
        
        # Assign tasks to different assignees
        await task_service.assign_task(
            task_id=task1.task_id,
            assignee="agent-1",
            assigned_by="integration-test"
        )
        
        await task_service.assign_task(
            task_id=task2.task_id,
            assignee="agent-2",
            assigned_by="integration-test"
        )
        
        # Act - Find tasks by assignee
        agent1_tasks = await task_service.find_tasks_by_assignee("agent-1")
        agent2_tasks = await task_service.find_tasks_by_assignee("agent-2")
        
        # Assert
        assert len(agent1_tasks) == 1
        assert agent1_tasks[0].task_id == task1.task_id
        
        assert len(agent2_tasks) == 1
        assert agent2_tasks[0].task_id == task2.task_id 