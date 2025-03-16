import pytest
import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.task_management.infrastructure.mongo_task_repository import MongoTaskRepository
from src.task_management.application.task_service import TaskService


@pytest.fixture
async def mongo_client():
    """Create a MongoDB client for testing."""
    # Use test database
    mongo_uri = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database("test_aihive")
    
    # Clear existing data
    await db.tasks.delete_many({})
    
    yield client
    
    # Cleanup
    await db.tasks.delete_many({})
    client.close()


@pytest.fixture
async def task_repository(mongo_client):
    """Create a MongoDB task repository for testing."""
    repository = MongoTaskRepository()
    
    # Override the config to use test database
    repository.config = AsyncMock()
    repository.config.database = {
        "connection_uri": mongo_client.address,
        "database_name": "test_aihive"
    }
    
    # Connect to the database
    await repository.connect()
    
    yield repository
    
    # Cleanup
    await repository.disconnect()


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker for testing."""
    broker = AsyncMock(spec=MessageBroker)
    broker.publish_event = AsyncMock()
    broker.subscribe_to_event = AsyncMock()
    broker.publish_command = AsyncMock()
    broker.subscribe_to_command = AsyncMock()
    return broker


@pytest.fixture
async def task_service(task_repository, mock_message_broker):
    """Create a task service with real repository and mock message broker."""
    return TaskService(task_repository, mock_message_broker)


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
            new_status=TaskStatus.IN_PROGRESS.value,
            changed_by="test-agent",
            reason="Starting work"
        )
        
        # Assert 2
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Act 3 - Submit for review
        task = await task_service.update_task_status(
            task_id=task_id,
            new_status=TaskStatus.REVIEW.value,
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
            new_status=TaskStatus.ASSIGNED.value,
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