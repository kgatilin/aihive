"""
Unit tests for the Task Polling Service.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.product_definition.agents.task_polling_service import TaskPollingService


@pytest.fixture
def mock_task_service():
    """Create a mock task service."""
    task_service = AsyncMock()
    task_service.find_tasks_by_assignee = AsyncMock()
    task_service.update_task_status = AsyncMock()
    task_service.add_comment = AsyncMock()
    return task_service


@pytest.fixture
def mock_product_manager_agent():
    """Create a mock product manager agent."""
    agent = AsyncMock()
    agent.process_task = AsyncMock()
    return agent


@pytest.fixture
def task_polling_service(mock_task_service, mock_product_manager_agent):
    """Create a Task Polling Service instance for testing."""
    return TaskPollingService(
        task_service=mock_task_service,
        product_manager_agent=mock_product_manager_agent,
        agent_id="test_agent",
        poll_interval_seconds=0.1  # Short interval for testing
    )


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing."""
    return [
        Task(
            task_id="task-1",
            title="High Priority Task",
            description="This is a high priority task.",
            priority=TaskPriority.HIGH,
            status=TaskStatus.ASSIGNED,
            created_by="test_user",
            assignee="test_agent"
        ),
        Task(
            task_id="task-2",
            title="Medium Priority Task",
            description="This is a medium priority task.",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.REVIEW,
            created_by="test_user",
            assignee="test_agent"
        ),
        Task(
            task_id="task-3",
            title="Low Priority Task",
            description="This is a low priority task.",
            priority=TaskPriority.LOW,
            status=TaskStatus.ASSIGNED,
            created_by="test_user",
            assignee="test_agent"
        ),
        Task(
            task_id="task-4",
            title="Critical Priority Task",
            description="This is a critical priority task.",
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.BLOCKED,
            created_by="test_user",
            assignee="test_agent"
        )
    ]


@pytest.mark.asyncio
async def test_poll_tasks(task_polling_service, mock_task_service, sample_tasks):
    """Test polling for tasks."""
    # Configure the mock to return sample tasks
    mock_task_service.find_tasks_by_assignee.return_value = sample_tasks
    
    # Poll for tasks
    tasks = await task_polling_service.poll_tasks()
    
    # Verify that find_tasks_by_assignee was called
    mock_task_service.find_tasks_by_assignee.assert_called_once_with("test_agent")
    
    # Verify that all tasks were returned
    assert len(tasks) == 4
    assert all(task in sample_tasks for task in tasks)


@pytest.mark.asyncio
async def test_prioritize_tasks(task_polling_service, sample_tasks):
    """Test prioritizing tasks based on priority and status."""
    # Prioritize the tasks
    prioritized_tasks = await task_polling_service.prioritize_tasks(sample_tasks)
    
    # Verify the order of prioritized tasks
    # Critical priority with BLOCKED should be first
    assert prioritized_tasks[0].task_id == "task-4"
    
    # High priority should be next
    assert prioritized_tasks[1].task_id == "task-1"
    
    # Medium priority with REVIEW should be next
    assert prioritized_tasks[2].task_id == "task-2"
    
    # Low priority should be last
    assert prioritized_tasks[3].task_id == "task-3"


@pytest.mark.asyncio
async def test_get_next_task(task_polling_service, mock_task_service, sample_tasks):
    """Test getting the next highest priority task."""
    # Configure the mock to return sample tasks
    mock_task_service.find_tasks_by_assignee.return_value = sample_tasks
    
    # Get the next task
    next_task = await task_polling_service.get_next_task()
    
    # Verify that the highest priority task was returned
    assert next_task is not None
    assert next_task.task_id == "task-4"  # Critical priority with BLOCKED


@pytest.mark.asyncio
async def test_mark_task_as_in_progress(task_polling_service, mock_task_service, sample_tasks):
    """Test marking a task as in progress."""
    task = sample_tasks[0]  # High priority task
    
    # Configure the mock to return the task with updated status
    updated_task = Task(
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=TaskStatus.IN_PROGRESS,
        created_by=task.created_by,
        assignee=task.assignee
    )
    mock_task_service.update_task_status.return_value = updated_task
    
    # Mark the task as in progress
    result = await task_polling_service.mark_task_as_in_progress(task)
    
    # Verify that update_task_status was called
    mock_task_service.update_task_status.assert_called_once_with(
        task_id=task.task_id,
        new_status="in_progress",
        changed_by="test_agent",
        reason="Task processing started"
    )
    
    # Verify that the updated task was returned
    assert result is updated_task
    assert result.status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_mark_task_as_completed(task_polling_service, sample_tasks):
    """Test marking a task as completed."""
    task = sample_tasks[0]  # High priority task
    
    # Add the task to the processing_tasks dictionary
    task_polling_service._processing_tasks[task.task_id] = MagicMock()
    
    # Mark the task as completed
    result = await task_polling_service.mark_task_as_completed(task)
    
    # Verify that the task was removed from the processing_tasks dictionary
    assert task.task_id not in task_polling_service._processing_tasks
    
    # Verify that the task was returned
    assert result is task


@pytest.mark.asyncio
async def test_start_stop(task_polling_service):
    """Test starting and stopping the polling service."""
    # Start the polling service
    await task_polling_service.start()
    
    # Verify that the service is running
    assert task_polling_service.running is True
    assert task_polling_service._polling_task is not None
    
    # Stop the polling service
    await task_polling_service.stop()
    
    # Verify that the service is not running
    assert task_polling_service.running is False
    assert task_polling_service._polling_task is not None  # Task object still exists but is cancelled


@pytest.mark.asyncio
async def test_polling_loop_processes_tasks(task_polling_service, mock_task_service, mock_product_manager_agent, sample_tasks):
    """Test that the polling loop processes tasks."""
    # Configure the mock to return a single task
    mock_task_service.find_tasks_by_assignee.return_value = [sample_tasks[0]]
    
    # Configure the update_task_status to return the same task
    mock_task_service.update_task_status.return_value = sample_tasks[0]
    
    # Configure the process_task to return the same task
    mock_product_manager_agent.process_task.return_value = sample_tasks[0]
    
    # Start the polling service
    with patch.object(
        task_polling_service, '_process_task', wraps=task_polling_service._process_task
    ) as mock_process_task:
        await task_polling_service.start()
        
        # Wait for a short time to allow the polling loop to run
        await asyncio.sleep(0.2)
        
        # Stop the polling service
        await task_polling_service.stop()
        
        # Verify that find_tasks_by_assignee was called
        mock_task_service.find_tasks_by_assignee.assert_called_with("test_agent")
        
        # Verify that process_task was called
        mock_process_task.assert_called()


@pytest.mark.asyncio
async def test_process_task_calls_product_manager_agent(task_polling_service, mock_product_manager_agent, sample_tasks):
    """Test that _process_task calls the product manager agent."""
    task = sample_tasks[0]  # High priority task
    
    # Process the task
    await task_polling_service._process_task(task)
    
    # Verify that product_manager_agent.process_task was called
    mock_product_manager_agent.process_task.assert_called_once_with(task)


@pytest.mark.asyncio
async def test_process_task_handles_errors(task_polling_service, mock_product_manager_agent, mock_task_service, sample_tasks):
    """Test that _process_task handles errors."""
    task = sample_tasks[0]  # High priority task
    
    # Configure the mock to raise an exception
    mock_product_manager_agent.process_task.side_effect = Exception("Test error")
    
    # Process the task
    await task_polling_service._process_task(task)
    
    # Verify that add_comment was called to report the error
    mock_task_service.add_comment.assert_called_once_with(
        task_id=task.task_id,
        comment="Error processing task: Test error",
        created_by="test_agent"
    ) 