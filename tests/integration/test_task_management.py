import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from motor.motor_asyncio import AsyncIOMotorClient

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.infrastructure.repositories.mongodb_task_repository import MongoDBTaskRepository
from src.task_management.application.services.task_service import TaskService
from src.core.message_broker.message_broker_interface import MessageBroker


@pytest.fixture
async def mongodb_client():
    """Create a MongoDB client for testing."""
    # Use a test database
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    # Clear the test database before each test
    await client.aihive_test.tasks.delete_many({})
    yield client
    # Clean up after tests
    await client.aihive_test.tasks.delete_many({})
    client.close()


@pytest.fixture
async def task_repository(mongodb_client):
    """Create a task repository with the test MongoDB client."""
    repo = MongoDBTaskRepository(client=mongodb_client)
    # Override the database name to use the test database
    repo.db = mongodb_client.aihive_test
    repo.collection = repo.db.tasks
    # Create indexes
    await repo._create_indexes()
    return repo


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker."""
    broker = AsyncMock(spec=MessageBroker)
    broker.publish_event = AsyncMock()
    broker.subscribe_to_event = AsyncMock()
    return broker


@pytest.fixture
async def task_service(task_repository, mock_message_broker):
    """Create a task service with the test repository and mock broker."""
    return TaskService(task_repository, mock_message_broker)


@pytest.mark.asyncio
async def test_create_and_retrieve_task(task_service):
    """Test creating a task and retrieving it."""
    # Arrange
    title = "Integration Test Task"
    description = "This is an integration test task"
    
    # Act
    created_task = await task_service.create_task(
        title=title,
        description=description,
        priority="high",
        created_by="integration_test"
    )
    
    # Retrieve the task
    retrieved_task = await task_service.get_task(created_task.task_id)
    
    # Assert
    assert retrieved_task is not None
    assert retrieved_task.task_id == created_task.task_id
    assert retrieved_task.title == title
    assert retrieved_task.description == description
    assert retrieved_task.priority == TaskPriority.HIGH
    assert retrieved_task.created_by == "integration_test"
    assert retrieved_task.status == TaskStatus.CREATED


@pytest.mark.asyncio
async def test_task_lifecycle(task_service):
    """Test the complete lifecycle of a task."""
    # Create a task
    task = await task_service.create_task(
        title="Lifecycle Test Task",
        description="Testing the complete task lifecycle",
        priority="medium",
        created_by="integration_test"
    )
    
    # Assign the task
    task = await task_service.assign_task(
        task_id=task.task_id,
        assignee="test_assignee",
        assigned_by="integration_test"
    )
    assert task.assignee == "test_assignee"
    assert task.status == TaskStatus.ASSIGNED
    
    # Update status to IN_PROGRESS
    task = await task_service.update_task_status(
        task_id=task.task_id,
        new_status="in_progress",
        changed_by="test_assignee",
        reason="Starting work"
    )
    assert task.status == TaskStatus.IN_PROGRESS
    
    # Update status to REVIEW
    task = await task_service.update_task_status(
        task_id=task.task_id,
        new_status="review",
        changed_by="test_assignee",
        reason="Ready for review"
    )
    assert task.status == TaskStatus.REVIEW
    
    # Complete the task
    task = await task_service.complete_task(
        task_id=task.task_id,
        completed_by="test_reviewer",
        artifact_ids=["artifact-1", "artifact-2"],
        completion_notes="Completed successfully"
    )
    assert task.status == TaskStatus.COMPLETED
    
    # Retrieve the final task state
    final_task = await task_service.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED
    assert "artifact-1" in final_task.artifact_ids
    assert "artifact-2" in final_task.artifact_ids


@pytest.mark.asyncio
async def test_find_tasks_by_status(task_service):
    """Test finding tasks by status."""
    # Create tasks with different statuses
    task1 = await task_service.create_task(
        title="Task 1",
        description="First test task",
        priority="low",
        created_by="integration_test"
    )
    
    task2 = await task_service.create_task(
        title="Task 2",
        description="Second test task",
        priority="medium",
        created_by="integration_test"
    )
    
    # Assign and start task2
    await task_service.assign_task(
        task_id=task2.task_id,
        assignee="test_assignee",
        assigned_by="integration_test"
    )
    
    await task_service.update_task_status(
        task_id=task2.task_id,
        new_status="in_progress",
        changed_by="test_assignee"
    )
    
    # Find tasks by status
    created_tasks = await task_service.find_tasks_by_status("created")
    in_progress_tasks = await task_service.find_tasks_by_status("in_progress")
    
    # Assert
    assert len(created_tasks) == 1
    assert created_tasks[0].task_id == task1.task_id
    
    assert len(in_progress_tasks) == 1
    assert in_progress_tasks[0].task_id == task2.task_id


@pytest.mark.asyncio
async def test_find_tasks_by_assignee(task_service):
    """Test finding tasks by assignee."""
    # Create tasks and assign to different users
    task1 = await task_service.create_task(
        title="Task for User A",
        description="Task assigned to User A",
        priority="medium",
        created_by="integration_test"
    )
    
    task2 = await task_service.create_task(
        title="Task for User B",
        description="Task assigned to User B",
        priority="high",
        created_by="integration_test"
    )
    
    # Assign tasks
    await task_service.assign_task(
        task_id=task1.task_id,
        assignee="user_a",
        assigned_by="integration_test"
    )
    
    await task_service.assign_task(
        task_id=task2.task_id,
        assignee="user_b",
        assigned_by="integration_test"
    )
    
    # Find tasks by assignee
    user_a_tasks = await task_service.find_tasks_by_assignee("user_a")
    user_b_tasks = await task_service.find_tasks_by_assignee("user_b")
    
    # Assert
    assert len(user_a_tasks) == 1
    assert user_a_tasks[0].task_id == task1.task_id
    
    assert len(user_b_tasks) == 1
    assert user_b_tasks[0].task_id == task2.task_id 