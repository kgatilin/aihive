"""
Unit tests for the orchestrator agent module.

These tests verify the functionality of the OrchestratorAgent base class
and the ProductRefinementOrchestrator concrete implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional

from src.orchestration.domain.orchestrator_agent import OrchestratorAgent, ProductRefinementOrchestrator
from src.task_management.domain.task import Task, TaskStatus
from src.task_management.application.task_service import TaskService


class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent abstract base class."""
    
    class ConcreteOrchestratorAgent(OrchestratorAgent):
        """Concrete implementation of abstract base class for testing."""
        
        async def subscribe_to_events(self) -> None:
            """Test implementation of abstract method."""
            self.events_subscribed = True
        
        async def poll_tasks(self) -> None:
            """Test implementation of abstract method."""
            self.tasks_polled = True
    
    @pytest.fixture
    def task_service_mock(self):
        """Create a mock task service."""
        return AsyncMock(spec=TaskService)
    
    @pytest.fixture
    def message_broker_mock(self):
        """Create a mock message broker."""
        return AsyncMock()
    
    @pytest.fixture
    def agent(self, task_service_mock, message_broker_mock):
        """Create a concrete orchestrator agent for testing."""
        agent = self.ConcreteOrchestratorAgent(task_service_mock, message_broker_mock)
        agent.poll_interval = 0.01  # Short interval for testing
        agent.events_subscribed = False
        agent.tasks_polled = False
        return agent
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent, task_service_mock, message_broker_mock):
        """Test that the agent initializes correctly."""
        assert agent.task_service == task_service_mock
        assert agent.message_broker == message_broker_mock
        assert agent.running is False
        assert agent.poll_interval == 0.01
    
    @pytest.mark.asyncio
    async def test_start(self, agent):
        """Test starting the agent."""
        await agent.start()
        assert agent.running is True
        assert agent.events_subscribed is True
        
        # Wait for polling loop to execute at least once
        await asyncio.sleep(0.02)
        assert agent.tasks_polled is True
        
        # Stop the agent to clean up
        await agent.stop()
    
    @pytest.mark.asyncio
    async def test_start_already_running(self, agent):
        """Test starting an agent that's already running."""
        agent.running = True
        await agent.start()
        assert agent.events_subscribed is False  # Should not have changed
        
        # Set back to not running for cleanup
        agent.running = False
    
    @pytest.mark.asyncio
    async def test_stop(self, agent):
        """Test stopping the agent."""
        agent.running = True
        await agent.stop()
        assert agent.running is False
    
    @pytest.mark.asyncio
    async def test_stop_not_running(self, agent):
        """Test stopping an agent that's not running."""
        agent.running = False
        await agent.stop()
        assert agent.running is False
    
    @pytest.mark.asyncio
    async def test_polling_loop_handles_exceptions(self, agent, monkeypatch):
        """Test that polling loop handles exceptions gracefully."""
        # Make poll_tasks raise an exception
        async def mock_poll_tasks():
            raise Exception("Test exception")
        
        monkeypatch.setattr(agent, "poll_tasks", mock_poll_tasks)
        
        # Start agent
        await agent.start()
        assert agent.running is True
        
        # Wait for polling loop to execute at least once
        await asyncio.sleep(0.02)
        
        # Agent should still be running despite exception
        assert agent.running is True
        
        # Stop the agent to clean up
        await agent.stop()


class TestProductRefinementOrchestrator:
    """Test cases for ProductRefinementOrchestrator."""
    
    @pytest.fixture
    def task_service_mock(self):
        """Create a mock task service."""
        return AsyncMock(spec=TaskService)
    
    @pytest.fixture
    def message_broker_mock(self):
        """Create a mock message broker."""
        return AsyncMock()
    
    @pytest.fixture
    def orchestrator(self, task_service_mock, message_broker_mock):
        """Create a ProductRefinementOrchestrator instance."""
        orchestrator = ProductRefinementOrchestrator(task_service_mock, message_broker_mock)
        # Check the default poll_interval value is 300 before modifying it for tests
        assert orchestrator.poll_interval == 300  # Default is 5 minutes
        orchestrator.poll_interval = 0.01  # Short interval for testing
        return orchestrator
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task."""
        task = AsyncMock(spec=Task)
        task.task_id = "test-task-id"
        task.title = "Test Task"
        task.status = TaskStatus.REVIEW
        task.tags = ["product_refinement"]
        task.priority = MagicMock()
        task.priority.value = "medium"
        task.assignee = None
        return task
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator, task_service_mock, message_broker_mock):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.task_service == task_service_mock
        assert orchestrator.message_broker == message_broker_mock
        assert orchestrator.poll_interval == 0.01  # Modified for testing
    
    @pytest.mark.asyncio
    async def test_subscribe_to_events(self, orchestrator, message_broker_mock):
        """Test subscription to events."""
        await orchestrator.subscribe_to_events()
        
        # Verify that we subscribed to the expected events
        message_broker_mock.subscribe_to_event.assert_any_call(
            "task.status_changed",
            orchestrator._handle_task_status_change
        )
        
        message_broker_mock.subscribe_to_event.assert_any_call(
            "task.created",
            orchestrator._handle_task_created
        )
    
    @pytest.mark.asyncio
    async def test_handle_task_status_change_review(self, orchestrator, monkeypatch):
        """Test handling a task status change to REVIEW."""
        # Mock the _process_task_in_review method
        process_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "_process_task_in_review", process_mock)
        
        # Call the handler with a valid event
        event = {
            "task_id": "test-task-id",
            "new_status": TaskStatus.REVIEW.value
        }
        await orchestrator._handle_task_status_change(event)
        
        # Verify that _process_task_in_review was called
        process_mock.assert_called_once_with("test-task-id")
    
    @pytest.mark.asyncio
    async def test_handle_task_status_change_invalid(self, orchestrator, monkeypatch):
        """Test handling an invalid task status change event."""
        # Mock the _process_task_in_review method
        process_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "_process_task_in_review", process_mock)
        
        # Call the handler with an invalid event
        event = {"task_id": "test-task-id"}  # Missing new_status
        await orchestrator._handle_task_status_change(event)
        
        # Verify that _process_task_in_review was not called
        process_mock.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_task_status_change_not_review(self, orchestrator, monkeypatch):
        """Test handling a task status change to a status other than REVIEW."""
        # Mock the _process_task_in_review method
        process_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "_process_task_in_review", process_mock)
        
        # Call the handler with a valid event for a different status
        event = {
            "task_id": "test-task-id",
            "new_status": TaskStatus.COMPLETED.value
        }
        await orchestrator._handle_task_status_change(event)
        
        # Verify that _process_task_in_review was not called
        process_mock.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_task_created_product_refinement(self, orchestrator, task_service_mock, sample_task):
        """Test handling a task created event for a product refinement task."""
        # Set up the task service to return our sample task
        task_service_mock.get_task.return_value = sample_task
        
        # Call the handler with a valid event
        event = {"task_id": "test-task-id"}
        await orchestrator._handle_task_created(event)
        
        # Verify that task_service.assign_task was called
        task_service_mock.assign_task.assert_called_once_with(
            "test-task-id",
            "product_owner",
            "orchestrator"
        )
    
    @pytest.mark.asyncio
    async def test_handle_task_created_not_product_refinement(self, orchestrator, task_service_mock, sample_task):
        """Test handling a task created event for a non-product-refinement task."""
        # Modify the sample task to not have the product_refinement tag
        sample_task.tags = ["other_tag"]
        task_service_mock.get_task.return_value = sample_task
        
        # Call the handler with a valid event
        event = {"task_id": "test-task-id"}
        await orchestrator._handle_task_created(event)
        
        # Verify that task_service.assign_task was not called
        task_service_mock.assign_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_task_created_already_assigned(self, orchestrator, task_service_mock, sample_task):
        """Test handling a task created event for a task that's already assigned."""
        # Modify the sample task to be already assigned
        sample_task.assignee = "existing_assignee"
        task_service_mock.get_task.return_value = sample_task
        
        # Call the handler with a valid event
        event = {"task_id": "test-task-id"}
        await orchestrator._handle_task_created(event)
        
        # Verify that task_service.assign_task was not called
        task_service_mock.assign_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_task_created_invalid(self, orchestrator, task_service_mock):
        """Test handling an invalid task created event."""
        # Call the handler with an invalid event
        event = {}  # Missing task_id
        await orchestrator._handle_task_created(event)
        
        # Verify that task_service.get_task was not called
        task_service_mock.get_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_task_in_review(self, orchestrator, task_service_mock, sample_task):
        """Test processing a task in review."""
        # Set up the task service to return our sample task
        task_service_mock.get_task.return_value = sample_task
        
        # Call the method
        await orchestrator._process_task_in_review("test-task-id")
        
        # Verify that task_service.create_task was called
        task_service_mock.create_task.assert_called_once()
        call_kwargs = task_service_mock.create_task.call_args.kwargs
        assert call_kwargs["title"].startswith("Review product refinement:")
        assert call_kwargs["parent_task_id"] == "test-task-id"
        assert "review" in call_kwargs["tags"]
        assert "product_refinement" in call_kwargs["tags"]
    
    @pytest.mark.asyncio
    async def test_process_task_in_review_not_found(self, orchestrator, task_service_mock):
        """Test processing a task in review that doesn't exist."""
        # Set up the task service to return None
        task_service_mock.get_task.return_value = None
        
        # Call the method
        await orchestrator._process_task_in_review("test-task-id")
        
        # Verify that task_service.create_task was not called
        task_service_mock.create_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_task_in_review_not_product_refinement(self, orchestrator, task_service_mock, sample_task):
        """Test processing a task in review that's not a product refinement task."""
        # Modify the sample task to not have the product_refinement tag
        sample_task.tags = ["other_tag"]
        task_service_mock.get_task.return_value = sample_task
        
        # Call the method
        await orchestrator._process_task_in_review("test-task-id")
        
        # Verify that task_service.create_task was not called
        task_service_mock.create_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_poll_tasks(self, orchestrator, task_service_mock, sample_task):
        """Test polling tasks."""
        # Set up the task service to return our sample task
        task_service_mock.find_tasks_by_status.return_value = [sample_task]
        
        # Call the method
        await orchestrator.poll_tasks()
        
        # Verify that task_service.find_tasks_by_status was called with REVIEW
        task_service_mock.find_tasks_by_status.assert_called_once_with(TaskStatus.REVIEW.value)
    
    @pytest.mark.asyncio
    async def test_determine_next_task_requirement_gathering(self, orchestrator, task_service_mock, sample_task):
        """Test determining the next task for a requirement gathering task."""
        # Modify the sample task to include the requirement_gathering tag
        sample_task.tags = ["product_refinement", "requirement_gathering"]
        task_service_mock.get_task.return_value = sample_task
        
        # Set up the return value for create_task
        new_task = AsyncMock(spec=Task)
        new_task.task_id = "new-task-id"
        task_service_mock.create_task.return_value = new_task
        
        # Call the method
        result = await orchestrator.determine_next_task("test-task-id")
        
        # Verify that task_service.create_task was called and the result is correct
        task_service_mock.create_task.assert_called_once()
        call_kwargs = task_service_mock.create_task.call_args.kwargs
        assert call_kwargs["title"].startswith("Design for:")
        assert call_kwargs["parent_task_id"] == "test-task-id"
        assert "design" in call_kwargs["tags"]
        assert result == "new-task-id"
    
    @pytest.mark.asyncio
    async def test_determine_next_task_not_requirement_gathering(self, orchestrator, task_service_mock, sample_task):
        """Test determining the next task for a non-requirement-gathering task."""
        # Sample task already has product_refinement tag but not requirement_gathering
        task_service_mock.get_task.return_value = sample_task
        
        # Call the method
        result = await orchestrator.determine_next_task("test-task-id")
        
        # Verify that task_service.create_task was not called and no next task
        task_service_mock.create_task.assert_not_called()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_determine_next_task_not_product_refinement(self, orchestrator, task_service_mock, sample_task):
        """Test determining the next task for a non-product-refinement task."""
        # Modify the sample task to not have the product_refinement tag
        sample_task.tags = ["other_tag"]
        task_service_mock.get_task.return_value = sample_task
        
        # Call the method
        result = await orchestrator.determine_next_task("test-task-id")
        
        # Verify that result is None
        assert result is None
    
    @pytest.mark.asyncio
    async def test_determine_next_task_not_found(self, orchestrator, task_service_mock):
        """Test determining the next task for a task that doesn't exist."""
        # Set up the task service to return None
        task_service_mock.get_task.return_value = None
        
        # Call the method
        result = await orchestrator.determine_next_task("test-task-id")
        
        # Verify that result is None
        assert result is None 