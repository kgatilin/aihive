"""
Unit tests for the domain interfaces in the product definition domain.

These tests verify that concrete implementations of interfaces correctly
implement all the required abstract methods.
"""

import pytest
from unittest.mock import AsyncMock
from typing import Dict, Any, List, Optional

from src.product_definition.domain.product_manager_agent_interface import ProductManagerAgentInterface
from src.product_definition.domain.task_polling_service_interface import TaskPollingServiceInterface
from src.task_management.domain.entities.task import Task


class TestProductManagerAgentInterface:
    """Tests for the ProductManagerAgentInterface."""
    
    class ConcreteProductManagerAgent(ProductManagerAgentInterface):
        """Concrete implementation of the interface for testing."""
        
        async def process_task(self, task: Task) -> Task:
            """Implement abstract method."""
            return task
        
        async def analyze_user_request(self, task: Task) -> Dict[str, Any]:
            """Implement abstract method."""
            return {"analyzed": True}
        
        async def determine_if_clarification_needed(self, task: Task, analysis: Dict[str, Any]) -> bool:
            """Implement abstract method."""
            return False
        
        async def generate_clarification_questions(self, task: Task, analysis: Dict[str, Any]) -> List[str]:
            """Implement abstract method."""
            return ["Question 1", "Question 2"]
        
        async def process_clarification_response(self, task: Task, response: str) -> Dict[str, Any]:
            """Implement abstract method."""
            return {"response_processed": True}
        
        async def create_product_requirement_document(self, task: Task, analysis: Dict[str, Any]) -> str:
            """Implement abstract method."""
            return "PRD Content"
        
        async def validate_product_requirement_document(self, prd_content: str) -> bool:
            """Implement abstract method."""
            return True
    
    def test_create_concrete_implementation(self):
        """Test that we can create a concrete implementation of the interface."""
        agent = self.ConcreteProductManagerAgent()
        assert isinstance(agent, ProductManagerAgentInterface)
    
    @pytest.mark.asyncio
    async def test_process_task(self):
        """Test the process_task method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        result = await agent.process_task(task)
        assert result == task
    
    @pytest.mark.asyncio
    async def test_analyze_user_request(self):
        """Test the analyze_user_request method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        result = await agent.analyze_user_request(task)
        assert result == {"analyzed": True}
    
    @pytest.mark.asyncio
    async def test_determine_if_clarification_needed(self):
        """Test the determine_if_clarification_needed method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        analysis = {"data": "test"}
        result = await agent.determine_if_clarification_needed(task, analysis)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self):
        """Test the generate_clarification_questions method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        analysis = {"data": "test"}
        result = await agent.generate_clarification_questions(task, analysis)
        assert result == ["Question 1", "Question 2"]
    
    @pytest.mark.asyncio
    async def test_process_clarification_response(self):
        """Test the process_clarification_response method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        response = "User response"
        result = await agent.process_clarification_response(task, response)
        assert result == {"response_processed": True}
    
    @pytest.mark.asyncio
    async def test_create_product_requirement_document(self):
        """Test the create_product_requirement_document method."""
        agent = self.ConcreteProductManagerAgent()
        task = AsyncMock(spec=Task)
        analysis = {"data": "test"}
        result = await agent.create_product_requirement_document(task, analysis)
        assert result == "PRD Content"
    
    @pytest.mark.asyncio
    async def test_validate_product_requirement_document(self):
        """Test the validate_product_requirement_document method."""
        agent = self.ConcreteProductManagerAgent()
        result = await agent.validate_product_requirement_document("PRD Content")
        assert result is True


class TestTaskPollingServiceInterface:
    """Tests for the TaskPollingServiceInterface."""
    
    class ConcreteTaskPollingService(TaskPollingServiceInterface):
        """Concrete implementation of the interface for testing."""
        
        async def start(self) -> None:
            """Implement abstract method."""
            self.running = True
        
        async def stop(self) -> None:
            """Implement abstract method."""
            self.running = False
        
        async def poll_tasks(self) -> List[Task]:
            """Implement abstract method."""
            task = AsyncMock(spec=Task)
            return [task]
        
        async def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
            """Implement abstract method."""
            return sorted(tasks, key=lambda t: id(t))
        
        async def get_next_task(self) -> Optional[Task]:
            """Implement abstract method."""
            tasks = await self.poll_tasks()
            return tasks[0] if tasks else None
        
        async def mark_task_as_in_progress(self, task: Task) -> Task:
            """Implement abstract method."""
            return task
        
        async def mark_task_as_completed(self, task: Task) -> Task:
            """Implement abstract method."""
            return task
    
    def test_create_concrete_implementation(self):
        """Test that we can create a concrete implementation of the interface."""
        service = self.ConcreteTaskPollingService()
        assert isinstance(service, TaskPollingServiceInterface)
    
    @pytest.mark.asyncio
    async def test_start(self):
        """Test the start method."""
        service = self.ConcreteTaskPollingService()
        await service.start()
        assert getattr(service, "running", False) is True
    
    @pytest.mark.asyncio
    async def test_stop(self):
        """Test the stop method."""
        service = self.ConcreteTaskPollingService()
        await service.start()
        await service.stop()
        assert getattr(service, "running", True) is False
    
    @pytest.mark.asyncio
    async def test_poll_tasks(self):
        """Test the poll_tasks method."""
        service = self.ConcreteTaskPollingService()
        result = await service.poll_tasks()
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Task)
    
    @pytest.mark.asyncio
    async def test_prioritize_tasks(self):
        """Test the prioritize_tasks method."""
        service = self.ConcreteTaskPollingService()
        tasks = [AsyncMock(spec=Task), AsyncMock(spec=Task)]
        result = await service.prioritize_tasks(tasks)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] in tasks
        assert result[1] in tasks
    
    @pytest.mark.asyncio
    async def test_get_next_task(self):
        """Test the get_next_task method."""
        service = self.ConcreteTaskPollingService()
        result = await service.get_next_task()
        assert isinstance(result, Task)
    
    @pytest.mark.asyncio
    async def test_mark_task_as_in_progress(self):
        """Test the mark_task_as_in_progress method."""
        service = self.ConcreteTaskPollingService()
        task = AsyncMock(spec=Task)
        result = await service.mark_task_as_in_progress(task)
        assert result == task
    
    @pytest.mark.asyncio
    async def test_mark_task_as_completed(self):
        """Test the mark_task_as_completed method."""
        service = self.ConcreteTaskPollingService()
        task = AsyncMock(spec=Task)
        result = await service.mark_task_as_completed(task)
        assert result == task 