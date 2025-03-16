import logging
import asyncio
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from src.config import Config
from src.core.common.message_broker import MessageBroker
from src.task_management.domain.task import Task, TaskStatus
from src.task_management.domain.task_repository import TaskRepository
from src.task_management.application.task_service import TaskService


logger = logging.getLogger(__name__)


class OrchestratorAgent(ABC):
    """Abstract base class for orchestrator agents that manage task progression."""
    
    def __init__(self, 
                 message_broker: MessageBroker,
                 task_service: TaskService):
        self.config = Config()
        self.message_broker = message_broker
        self.task_service = task_service
        self.polling_interval = self.config.agent["polling_interval_seconds"]
        self.max_concurrent_tasks = self.config.agent["max_concurrent_tasks"]
        self._running = False
        self._current_tasks = set()  # Set of task IDs currently being processed
    
    async def start(self) -> None:
        """Start the orchestrator agent."""
        if self._running:
            logger.warning("Orchestrator agent is already running.")
            return
        
        self._running = True
        logger.info(f"Starting orchestrator agent with polling interval {self.polling_interval}s")
        
        # Subscribe to relevant events
        await self._subscribe_to_events()
        
        # Start the main polling loop
        asyncio.create_task(self._poll_tasks())
    
    async def stop(self) -> None:
        """Stop the orchestrator agent."""
        if not self._running:
            logger.warning("Orchestrator agent is not running.")
            return
        
        self._running = False
        logger.info("Stopping orchestrator agent.")
    
    async def _poll_tasks(self) -> None:
        """Periodically check for tasks that need to be processed."""
        while self._running:
            try:
                # Only process new tasks if we're below the concurrency limit
                if len(self._current_tasks) < self.max_concurrent_tasks:
                    # Find tasks that need processing
                    available_slots = self.max_concurrent_tasks - len(self._current_tasks)
                    await self._find_and_process_tasks(available_slots)
                
                # Wait for the next polling interval
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                logger.error(f"Error in orchestrator polling loop: {str(e)}")
                # Continue the loop despite errors
                await asyncio.sleep(self.polling_interval)
    
    async def _find_and_process_tasks(self, max_tasks: int) -> None:
        """Find tasks that need to be processed and start processing them."""
        # Implementation will depend on the specific orchestrator's logic
        # This should be overridden by subclasses
        pass
    
    async def _subscribe_to_events(self) -> None:
        """Subscribe to relevant domain events."""
        # Subscribe to TaskCreatedEvent
        await self.message_broker.subscribe_to_event(
            "task.created",
            self._handle_task_created_event,
            f"orchestrator-task-created-{id(self)}"
        )
        
        # Subscribe to TaskStatusChangedEvent
        await self.message_broker.subscribe_to_event(
            "task.status_changed",
            self._handle_task_status_changed_event,
            f"orchestrator-task-status-changed-{id(self)}"
        )
        
        # Subscribe to TaskCompletedEvent
        await self.message_broker.subscribe_to_event(
            "task.completed",
            self._handle_task_completed_event,
            f"orchestrator-task-completed-{id(self)}"
        )
    
    async def _handle_task_created_event(self, event: Any) -> None:
        """Handle a task created event."""
        logger.info(f"Orchestrator received task.created event for task {event.task_id}")
        # Default implementation can be overridden by subclasses
    
    async def _handle_task_status_changed_event(self, event: Any) -> None:
        """Handle a task status changed event."""
        logger.info(f"Orchestrator received task.status_changed event for task {event.task_id}: {event.previous_status} -> {event.new_status}")
        # Default implementation can be overridden by subclasses
    
    async def _handle_task_completed_event(self, event: Any) -> None:
        """Handle a task completed event."""
        logger.info(f"Orchestrator received task.completed event for task {event.task_id}")
        # Remove the task from current tasks if it's there
        self._current_tasks.discard(event.task_id)
        # Default implementation can be overridden by subclasses
    
    @abstractmethod
    async def process_task(self, task: Task) -> None:
        """Process a single task. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def determine_next_step(self, task: Task) -> Optional[str]:
        """Determine the next step for a task. Must be implemented by subclasses.
        
        Returns:
            Optional[str]: The next action to take, or None if no action needed
        """
        pass


class ProductRefinementOrchestrator(OrchestratorAgent):
    """Orchestrator implementation for the Product Refinement workflow."""
    
    async def _find_and_process_tasks(self, max_tasks: int) -> None:
        """Find tasks ready for product refinement and process them."""
        # Look for tasks in CREATED state that haven't been assigned yet
        created_tasks = await self.task_service.find_tasks_by_status(TaskStatus.CREATED.value)
        created_tasks = [t for t in created_tasks if t.task_id not in self._current_tasks]
        
        # Look for tasks in ASSIGNED state that haven't been started
        assigned_tasks = await self.task_service.find_tasks_by_status(TaskStatus.ASSIGNED.value)
        assigned_tasks = [t for t in assigned_tasks if t.task_id not in self._current_tasks]
        
        # Combine and sort by priority, creation date, etc.
        # For simplicity, we'll just take the first max_tasks
        tasks_to_process = (created_tasks + assigned_tasks)[:max_tasks]
        
        # Process each task
        for task in tasks_to_process:
            # Mark this task as being processed
            self._current_tasks.add(task.task_id)
            
            # Start a new task to process this
            asyncio.create_task(self._process_task_with_error_handling(task))
    
    async def _process_task_with_error_handling(self, task: Task) -> None:
        """Process a task with error handling."""
        try:
            await self.process_task(task)
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
        finally:
            # Remove the task from current tasks
            self._current_tasks.discard(task.task_id)
    
    async def process_task(self, task: Task) -> None:
        """Process a task in the product refinement workflow."""
        logger.info(f"ProductRefinementOrchestrator processing task {task.task_id}: {task.title}")
        
        # Determine what needs to be done next for this task
        next_action = await self.determine_next_step(task)
        
        if next_action == "assign_to_product_agent":
            # Assign to product agent if it's a new task
            await self.task_service.assign_task(
                task_id=task.task_id,
                assignee="product_agent",
                assigned_by="orchestrator",
                reason="Auto-assigned for requirement refinement"
            )
        elif next_action == "start_requirement_refinement":
            # Change status to IN_PROGRESS and trigger product agent
            await self.task_service.update_task_status(
                task_id=task.task_id,
                new_status=TaskStatus.IN_PROGRESS.value,
                changed_by="orchestrator",
                reason="Starting requirement refinement"
            )
            
            # Publish command for product agent to begin refinement
            await self.message_broker.publish_command(
                "product.refine_requirement",
                {
                    "task_id": task.task_id,
                    "priority": task.priority.value
                }
            )
    
    async def determine_next_step(self, task: Task) -> Optional[str]:
        """Determine the next step for a task in the product refinement workflow."""
        if task.status == TaskStatus.CREATED:
            return "assign_to_product_agent"
        elif task.status == TaskStatus.ASSIGNED and task.assignee == "product_agent":
            return "start_requirement_refinement"
        
        # No action needed for this task
        return None 