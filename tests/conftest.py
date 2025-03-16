import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task_repository import TaskRepository


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker for testing."""
    broker = AsyncMock(spec=MessageBroker)
    # Configure common methods
    broker.publish_event = AsyncMock()
    broker.subscribe_to_event = AsyncMock()
    broker.publish_command = AsyncMock()
    broker.subscribe_to_command = AsyncMock()
    return broker


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository for testing."""
    repo = AsyncMock(spec=TaskRepository)
    # Configure common methods
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.find_by_status = AsyncMock(return_value=[])
    repo.find_by_assignee = AsyncMock(return_value=[])
    repo.find_by_criteria = AsyncMock(return_value=[])
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_id="test-task-123",
        title="Test Task",
        description="This is a test task",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.CREATED,
        created_by="test-user",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_task_dict():
    """Create a sample task dictionary for testing."""
    return {
        "task_id": "test-task-123",
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "medium",
        "status": "created",
        "created_by": "test-user",
        "assignee": None,
        "due_date": None,
        "requirements_ids": [],
        "parent_task_id": None,
        "tags": [],
        "created_at": datetime(2023, 1, 1, 12, 0, 0),
        "updated_at": datetime(2023, 1, 1, 12, 0, 0)
    } 