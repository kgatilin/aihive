"""
This module implements the Task Polling Service that periodically polls for tasks
assigned to the Product Manager Agent.
"""

import logging
import asyncio
import traceback
from typing import List, Optional, Dict, Tuple

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.application.services.task_service import TaskService
from src.product_definition.domain.interfaces.task_polling_service_interface import TaskPollingServiceInterface
from src.product_definition.agents.product_manager_agent import ProductManagerAgent


logger = logging.getLogger(__name__)


class TaskPollingService(TaskPollingServiceInterface):
    """
    Implementation of the Task Polling Service that periodically polls for tasks
    assigned to the Product Manager Agent.
    """
    
    def __init__(
        self,
        task_service: TaskService,
        product_manager_agent: ProductManagerAgent,
        agent_id: str,
        poll_interval_seconds: float = 60.0
    ):
        """
        Initialize the Task Polling Service.
        
        Args:
            task_service: The task service for interacting with tasks
            product_manager_agent: The product manager agent to process tasks
            agent_id: The ID of the agent for task assignment
            poll_interval_seconds: The interval between polling in seconds
        """
        self._task_service = task_service
        self._product_manager_agent = product_manager_agent
        self._agent_id = agent_id
        self._poll_interval_seconds = poll_interval_seconds
        self._polling_task = None
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
    
    async def start(self) -> None:
        """
        Start the task polling service.
        This starts a background task that runs the polling loop.
        """
        if self.running:
            logger.warning("Task polling service is already running")
            return
        
        logger.info(f"Starting task polling service for agent {self._agent_id}")
        self.running = True
        self._polling_task = asyncio.create_task(self._polling_loop())
        logger.info(f"Task polling service started with interval {self._poll_interval_seconds} seconds")
    
    async def stop(self) -> None:
        """
        Stop the task polling service.
        This stops the polling loop and performs cleanup.
        """
        if not self.running:
            logger.warning("Task polling service is not running")
            return
        
        logger.info(f"Stopping task polling service for agent {self._agent_id}")
        self.running = False
        
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
        
        # Cancel any in-progress task processing
        for task_id, task in self._processing_tasks.items():
            logger.info(f"Cancelling processing of task {task_id}")
            task.cancel()
        
        # Wait for all processing tasks to complete or be cancelled
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks.values(), return_exceptions=True)
            self._processing_tasks.clear()
        
        logger.info("Task polling service stopped")
    
    async def poll_tasks(self) -> List[Task]:
        """
        Poll for tasks that are assigned to the agent but not yet processed.
        
        Returns:
            A list of tasks that need to be processed
        """
        logger.debug(f"Polling for tasks assigned to agent {self._agent_id}")
        
        # Get tasks assigned to this agent
        tasks = await self._task_service.find_tasks_by_assignee(self._agent_id)
        
        # Filter tasks that are in a state we can process
        processable_statuses = [
            TaskStatus.ASSIGNED,
            TaskStatus.REVIEW,
            TaskStatus.BLOCKED
        ]
        
        processable_tasks = [
            task for task in tasks
            if task.status in processable_statuses
        ]
        
        logger.debug(f"Found {len(processable_tasks)} processable tasks")
        return processable_tasks
    
    async def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Prioritize the list of tasks based on business rules.
        
        Args:
            tasks: The list of tasks to prioritize
            
        Returns:
            The prioritized list of tasks
        """
        if not tasks:
            return []
        
        # Define priority weights for task priorities and statuses
        priority_weights = {
            TaskPriority.CRITICAL: 100,
            TaskPriority.HIGH: 75,
            TaskPriority.MEDIUM: 50,
            TaskPriority.LOW: 25
        }
        
        status_weights = {
            TaskStatus.BLOCKED: 20,
            TaskStatus.REVIEW: 10,
            TaskStatus.ASSIGNED: 0
        }
        
        # Calculate scores for each task based on priority and status
        task_scores: List[Tuple[Task, float]] = []
        for task in tasks:
            priority_score = priority_weights.get(task.priority, 0)
            status_score = status_weights.get(task.status, 0)
            score = priority_score + status_score
            task_scores.append((task, score))
        
        # Sort tasks by score in descending order
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted tasks
        return [task for task, _ in task_scores]
    
    async def get_next_task(self) -> Optional[Task]:
        """
        Get the next highest priority task to process.
        
        Returns:
            The next task to process, or None if no tasks are available
        """
        tasks = await self.poll_tasks()
        if not tasks:
            return None
        
        prioritized_tasks = await self.prioritize_tasks(tasks)
        if not prioritized_tasks:
            return None
        
        return prioritized_tasks[0]
    
    async def mark_task_as_in_progress(self, task: Task) -> Task:
        """
        Mark a task as being in progress to prevent other agents from processing it.
        
        Args:
            task: The task to mark as in progress
            
        Returns:
            The updated task
        """
        logger.info(f"Marking task {task.task_id} as in progress")
        
        updated_task = await self._task_service.update_task_status(
            task_id=task.task_id,
            new_status="in_progress",
            changed_by=self._agent_id,
            reason="Task processing started"
        )
        
        return updated_task
    
    async def mark_task_as_completed(self, task: Task) -> Task:
        """
        Mark a task as completed after processing.
        In reality, the agent will update the status as appropriate based on the processing result.
        
        Args:
            task: The task to mark as completed
            
        Returns:
            The updated task
        """
        logger.info(f"Marking task {task.task_id} as processing completed")
        
        # Remove the task from the processing tasks dictionary
        if task.task_id in self._processing_tasks:
            del self._processing_tasks[task.task_id]
        
        return task
    
    async def _polling_loop(self) -> None:
        """Background loop that periodically polls for and processes tasks."""
        logger.info(f"Starting polling loop for agent {self._agent_id}")
        
        while self.running:
            try:
                # Get the next task to process
                next_task = await self.get_next_task()
                
                if next_task:
                    logger.info(f"Processing task {next_task.task_id}")
                    
                    # Mark the task as in progress
                    updated_task = await self.mark_task_as_in_progress(next_task)
                    
                    # Process the task in the background
                    process_task = asyncio.create_task(self._process_task(updated_task))
                    self._processing_tasks[updated_task.task_id] = process_task
                else:
                    logger.debug("No tasks to process")
            
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
                logger.debug(traceback.format_exc())
            
            # Wait for the polling interval
            await asyncio.sleep(self._poll_interval_seconds)
    
    async def _process_task(self, task: Task) -> None:
        """
        Process a task using the Product Manager Agent.
        
        Args:
            task: The task to process
        """
        logger.info(f"Processing task {task.task_id} using agent {self._agent_id}")
        
        try:
            # Process the task with the Product Manager Agent
            processed_task = await self._product_manager_agent.process_task(task)
            
            logger.info(f"Completed processing of task {task.task_id}, new status: {processed_task.status.value}")
            
            # Mark the task as completed in our tracking
            await self.mark_task_as_completed(processed_task)
        
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Add an error comment to the task
            await self._task_service.add_comment(
                task_id=task.task_id,
                comment=f"Error processing task: {str(e)}",
                created_by=self._agent_id
            )
            
            # Remove the task from the processing tasks dictionary
            if task.task_id in self._processing_tasks:
                del self._processing_tasks[task.task_id] 