import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import warnings

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.core.message_broker.message_broker_interface import MessageBroker
from src.task_management.domain.repositories.task_repository_interface import TaskRepositoryInterface

# Create pytest hooks to suppress specific warnings
def pytest_configure(config):
    """Configure pytest and suppress specific warnings."""
    # Suppress the asyncio fixture loop scope warning
    warnings.filterwarnings(
        "ignore", 
        message="The configuration option \"asyncio_default_fixture_loop_scope\" is unset",
        module="pytest_asyncio.plugin"
    )
    
    # Try to set asyncio default fixture loop scope to function
    plugin = config.pluginmanager.getplugin("asyncio")
    if plugin:
        plugin.asyncio_default_fixture_loop_scope = "function"

# Instead of defining a custom event_loop fixture, we'll let pytest-asyncio handle it

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
    repo = AsyncMock(spec=TaskRepositoryInterface)
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