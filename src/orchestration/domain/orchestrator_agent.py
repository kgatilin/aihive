import logging
import asyncio
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from src.config import Config
from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task import Task, TaskStatus
from src.task_management.domain.repositories.task_repository_interface import TaskRepositoryInterface
from src.task_management.application.task_service import TaskService


logger = logging.getLogger(__name__)


class OrchestratorAgent(ABC):
    """Base class for orchestrator agents that manage task progression."""
    
    def __init__(self, task_service: TaskService, message_broker: MessageBroker):
        """Initialize the orchestrator agent."""
        self.task_service = task_service
        self.message_broker = message_broker
        self.running = False
        self.poll_interval = 60  # Default polling interval in seconds
    
    async def start(self) -> None:
        """Start the orchestrator agent."""
        if self.running:
            logger.warning("Orchestrator agent is already running")
            return
        
        self.running = True
        logger.info(f"{self.__class__.__name__} started")
        
        # Subscribe to events
        await self.subscribe_to_events()
        
        # Start polling loop
        asyncio.create_task(self._polling_loop())
    
    async def stop(self) -> None:
        """Stop the orchestrator agent."""
        if not self.running:
            logger.warning("Orchestrator agent is not running")
            return
        
        self.running = False
        logger.info(f"{self.__class__.__name__} stopped")
    
    @abstractmethod
    async def subscribe_to_events(self) -> None:
        """Subscribe to relevant events."""
        pass
    
    @abstractmethod
    async def poll_tasks(self) -> None:
        """Poll for tasks that need attention."""
        pass
    
    async def _polling_loop(self) -> None:
        """Background polling loop for tasks."""
        while self.running:
            try:
                await self.poll_tasks()
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
            
            await asyncio.sleep(self.poll_interval)


class ProductRefinementOrchestrator(OrchestratorAgent):
    """Orchestrator agent that manages product refinement tasks."""
    
    def __init__(self, task_service: TaskService, message_broker: MessageBroker):
        """Initialize the product refinement orchestrator."""
        super().__init__(task_service, message_broker)
        self.poll_interval = 300  # Poll every 5 minutes
    
    async def subscribe_to_events(self) -> None:
        """Subscribe to relevant events for product refinement tasks."""
        # Subscribe to task status changes
        await self.message_broker.subscribe_to_event(
            "task.status_changed",
            self._handle_task_status_change
        )
        
        # Subscribe to task created events
        await self.message_broker.subscribe_to_event(
            "task.created",
            self._handle_task_created
        )
        
        logger.info("ProductRefinementOrchestrator subscribed to events")
    
    async def _handle_task_status_change(self, event: Dict[str, Any]) -> None:
        """Handle task status change events."""
        try:
            task_id = event.get("task_id")
            new_status = event.get("new_status")
            
            if not task_id or not new_status:
                logger.warning("Invalid task status change event")
                return
            
            # Check if we need to take action based on the new status
            if new_status == TaskStatus.REVIEW.value:
                await self._process_task_in_review(task_id)
        except Exception as e:
            logger.error(f"Error handling task status change: {str(e)}")
    
    async def _handle_task_created(self, event: Dict[str, Any]) -> None:
        """Handle task created events."""
        try:
            task_id = event.get("task_id")
            
            if not task_id:
                logger.warning("Invalid task created event")
                return
            
            # Check if this is a product refinement task based on tags
            task = await self.task_service.get_task(task_id)
            if task and "product_refinement" in task.tags:
                # Auto-assign to default user if not assigned
                if not task.assignee:
                    await self.task_service.assign_task(task_id, "product_owner", "orchestrator")
                    logger.info(f"Auto-assigned product refinement task {task_id} to product_owner")
        except Exception as e:
            logger.error(f"Error handling task created event: {str(e)}")
    
    async def _process_task_in_review(self, task_id: str) -> None:
        """Process a task that has been submitted for review."""
        try:
            # Get the task
            task = await self.task_service.get_task(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found for review processing")
                return
            
            # Check if this is a product refinement task
            if "product_refinement" not in task.tags:
                return
            
            # Notify reviewers
            logger.info(f"Product refinement task {task_id} is ready for review")
            
            # Create a review task if needed
            await self.task_service.create_task(
                title=f"Review product refinement: {task.title}",
                description=f"Review the product refinement task: {task.task_id} - {task.title}",
                priority="high",
                created_by="orchestrator",
                parent_task_id=task.task_id,
                tags=["review", "product_refinement"]
            )
        except Exception as e:
            logger.error(f"Error processing task in review: {str(e)}")
    
    async def poll_tasks(self) -> None:
        """Poll for product refinement tasks that need attention."""
        try:
            # Find tasks that have been in review for too long
            review_tasks = await self.task_service.find_tasks_by_status(TaskStatus.REVIEW.value)
            
            for task in review_tasks:
                # Check if this is a product refinement task
                if "product_refinement" not in task.tags:
                    continue
                
                # Check if the task has been in review for more than 48 hours
                # This would require more sophisticated time tracking in a real system
                logger.info(f"Checking review status for task {task.task_id}")
                
                # Additional orchestration logic would go here
        except Exception as e:
            logger.error(f"Error polling tasks: {str(e)}")
    
    async def determine_next_task(self, completed_task_id: str) -> Optional[str]:
        """Determine the next task based on a completed task."""
        try:
            # Get the completed task
            task = await self.task_service.get_task(completed_task_id)
            if not task:
                logger.warning(f"Completed task {completed_task_id} not found")
                return None
            
            # Check if this is a product refinement task
            if "product_refinement" not in task.tags:
                return None
            
            # Create follow-up tasks based on the task type
            if "requirement_gathering" in task.tags:
                # After gathering requirements, create a design task
                new_task = await self.task_service.create_task(
                    title=f"Design for: {task.title}",
                    description=f"Create design based on requirements from task {task.task_id}",
                    priority=task.priority.value,
                    created_by="orchestrator",
                    parent_task_id=task.task_id,
                    tags=["product_refinement", "design"]
                )
                return new_task.task_id
            
            # Other task progression logic would go here
            
            return None
        except Exception as e:
            logger.error(f"Error determining next task: {str(e)}")
            return None 