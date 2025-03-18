"""
Task Polling Service Module

This module implements the Task Polling Service, which polls for tasks assigned to
the Product Manager agent and processes them asynchronously.
"""

import logging
import time
import threading
import uuid
from typing import Dict, List, Any, Optional, Callable

from src.infrastructure.message_queue.message_queue import MessageQueue
from src.infrastructure.message_queue.domain_events import (
    EventType, CommandType, TaskStatus,
    create_event, create_command, serialize_command, serialize_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskPollingService:
    """
    Service responsible for polling tasks assigned to the Product Manager.
    
    This service runs in the background and periodically polls for assigned tasks,
    delegating their processing to the appropriate agent.
    """
    
    def __init__(self, message_queue: MessageQueue, product_manager_agent, poll_interval: int = 60):
        """
        Initialize the Task Polling Service.
        
        Args:
            message_queue: The message queue for publishing events and commands
            product_manager_agent: The agent responsible for processing tasks
            poll_interval: Time between polls in seconds (default: 60 seconds)
        """
        self.message_queue = message_queue
        self.product_manager_agent = product_manager_agent
        self.poll_interval = poll_interval
        self.running = False
        self.poll_thread = None
        self.processing_thread = None
        self.source_id = f"task_poller_{uuid.uuid4()}"
        self.currently_processing_task = None
        self.processing_lock = threading.Lock()
        
        logger.info(f"Initialized TaskPollingService with poll interval: {poll_interval}s")
        
        # Register event handlers
        self.message_queue.subscribe_to_events(
            [EventType.TASK_ASSIGNED.name, EventType.TASK_UNASSIGNED.name], 
            self._handle_task_assignment_events
        )
    
    def start(self):
        """Start the periodic task polling."""
        if self.running:
            logger.warning("Task polling service is already running")
            return
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._polling_loop)
        self.poll_thread.daemon = True
        self.poll_thread.start()
        
        logger.info("Started task polling service")
    
    def stop(self):
        """Stop the periodic task polling."""
        if not self.running:
            logger.warning("Task polling service is not running")
            return
        
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=10)
        
        with self.processing_lock:
            if self.processing_thread and self.processing_thread.is_alive():
                logger.warning("Waiting for task processing to complete")
                self.processing_thread.join(timeout=30)
                if self.processing_thread.is_alive():
                    logger.warning("Task processing did not complete within timeout")
        
        logger.info("Stopped task polling service")
    
    def _polling_loop(self):
        """Background thread for periodic task polling."""
        while self.running:
            try:
                with self.processing_lock:
                    if self.currently_processing_task is None:
                        self._poll_for_tasks()
                    else:
                        logger.info(f"Skipping poll because task {self.currently_processing_task} is still processing")
            except Exception as e:
                logger.error(f"Error during task polling: {e}")
            
            # Sleep until next poll
            time.sleep(self.poll_interval)
    
    def _poll_for_tasks(self):
        """Poll for tasks assigned to the Product Manager agent."""
        logger.info("Polling for assigned tasks")
        
        # Query for assigned tasks
        query_cmd = create_command(
            command_type=CommandType.QUERY_TASKS,
            payload={
                "assigned_to": "product_manager_pool",
                "status_in": [
                    TaskStatus.REQUEST_VALIDATION.value,
                    TaskStatus.PRD_DEVELOPMENT.value
                ]
            },
            source=self.source_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.QUERY_TASKS.name,
            payload=serialize_command(query_cmd)
        )
        
        # In a real implementation, this would be handled via callback from an event
        # For demonstration, we'll simulate task response
        assigned_tasks = self._simulate_assigned_tasks_response()
        
        if not assigned_tasks:
            logger.info("No tasks assigned to Product Manager")
            return
        
        # Find highest priority task
        highest_priority_task = self._find_highest_priority_task(assigned_tasks)
        
        if highest_priority_task:
            # Process the task asynchronously
            self._process_task_async(highest_priority_task)
    
    def _process_task_async(self, task: Dict[str, Any]):
        """
        Process a task asynchronously.
        
        Args:
            task: The task to process
        """
        logger.info(f"Starting asynchronous processing of task: {task['task_id']}")
        self.currently_processing_task = task['task_id']
        
        # Create processing thread
        self.processing_thread = threading.Thread(
            target=self._process_task_thread,
            args=(task,)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _process_task_thread(self, task: Dict[str, Any]):
        """
        Thread function for processing a task.
        
        Args:
            task: The task to process
        """
        try:
            # Update task status to PRD_DEVELOPMENT if currently in REQUEST_VALIDATION
            if task['status'] == TaskStatus.REQUEST_VALIDATION.value:
                status_cmd = create_command(
                    command_type=CommandType.UPDATE_TASK_STATUS,
                    payload={
                        "task_id": task["task_id"],
                        "new_status": TaskStatus.PRD_DEVELOPMENT.value,
                        "comment": "Task is now being processed by Product Manager"
                    },
                    source=self.source_id
                )
                self.message_queue.publish_command(
                    command_type=CommandType.UPDATE_TASK_STATUS.name,
                    payload=serialize_command(status_cmd)
                )
            
            # Delegate task processing to Product Manager Agent
            processing_result = self._delegate_to_product_manager(task)
            
            # Handle processing result
            if processing_result.get("needs_clarification", False):
                # Handle clarification request
                self._handle_clarification_request(task, processing_result)
            else:
                # Handle successful processing
                self._handle_successful_processing(task, processing_result)
            
        except Exception as e:
            logger.error(f"Error processing task {task['task_id']}: {e}")
            # Could add error handling and recovery here
        finally:
            with self.processing_lock:
                self.currently_processing_task = None
                self.processing_thread = None
    
    def _delegate_to_product_manager(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate task processing to the Product Manager Agent.
        
        Args:
            task: The task to process
            
        Returns:
            Processing result from the agent
        """
        logger.info(f"Delegating task {task['task_id']} to Product Manager Agent")
        
        try:
            # In a real implementation, this would call the agent's process_task method
            # For now, we'll simulate the response
            agent_result = self._simulate_product_manager_processing(task)
            logger.info(f"Product Manager Agent completed processing task {task['task_id']}")
            return agent_result
            
        except Exception as e:
            logger.error(f"Error in Product Manager Agent processing: {e}")
            return {"error": str(e)}
    
    def _handle_clarification_request(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        Handle a task that needs clarification.
        
        Args:
            task: The task being processed
            result: The processing result from the agent
        """
        logger.info(f"Task {task['task_id']} needs clarification")
        
        # Add clarification questions as comment
        comment_cmd = create_command(
            command_type=CommandType.ADD_TASK_COMMENT,
            payload={
                "task_id": task["task_id"],
                "comment": "Clarification needed from user",
                "clarification_questions": result.get("clarification_questions", [])
            },
            source=self.source_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.ADD_TASK_COMMENT.name,
            payload=serialize_command(comment_cmd)
        )
        
        # Update task status to CLARIFICATION_NEEDED
        status_cmd = create_command(
            command_type=CommandType.UPDATE_TASK_STATUS,
            payload={
                "task_id": task["task_id"],
                "new_status": TaskStatus.CLARIFICATION_NEEDED.value,
                "comment": "Task needs clarification from user"
            },
            source=self.source_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.UPDATE_TASK_STATUS.name,
            payload=serialize_command(status_cmd)
        )
        
        # Publish clarification requested event
        clarification_event = create_event(
            event_type=EventType.CLARIFICATION_REQUESTED,
            payload={
                "task_id": task["task_id"],
                "questions": result.get("clarification_questions", [])
            },
            source=self.source_id
        )
        self.message_queue.publish_event(
            event_type=EventType.CLARIFICATION_REQUESTED.name,
            payload=serialize_event(clarification_event)
        )
    
    def _handle_successful_processing(self, task: Dict[str, Any], result: Dict[str, Any]):
        """
        Handle a successfully processed task.
        
        Args:
            task: The task being processed
            result: The processing result from the agent
        """
        logger.info(f"Task {task['task_id']} was successfully processed")
        
        # Store PRD document (this would be handled by a product requirement repository)
        prd_data = result.get("prd_data", {})
        prd_id = str(uuid.uuid4())
        
        # Publish Product Requirement Created event
        prd_event = create_event(
            event_type=EventType.PRODUCT_REQUIREMENT_CREATED,
            payload={
                "prd_id": prd_id,
                "task_id": task["task_id"],
                "prd_data": prd_data
            },
            source=self.source_id
        )
        self.message_queue.publish_event(
            event_type=EventType.PRODUCT_REQUIREMENT_CREATED.name,
            payload=serialize_event(prd_event)
        )
        
        # Link requirement to task
        link_cmd = create_command(
            command_type=CommandType.LINK_REQUIREMENT_TO_TASK,
            payload={
                "task_id": task["task_id"],
                "requirement_id": prd_id,
                "link_type": "primary"
            },
            source=self.source_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.LINK_REQUIREMENT_TO_TASK.name,
            payload=serialize_command(link_cmd)
        )
        
        # Update task status to PRD_VALIDATION
        status_cmd = create_command(
            command_type=CommandType.UPDATE_TASK_STATUS,
            payload={
                "task_id": task["task_id"],
                "new_status": TaskStatus.PRD_VALIDATION.value,
                "comment": "PRD is ready for validation"
            },
            source=self.source_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.UPDATE_TASK_STATUS.name,
            payload=serialize_command(status_cmd)
        )
        
        # Publish Human Validation Requested event
        validation_event = create_event(
            event_type=EventType.HUMAN_VALIDATION_REQUESTED,
            payload={
                "task_id": task["task_id"],
                "prd_id": prd_id,
                "validation_type": "prd_review"
            },
            source=self.source_id
        )
        self.message_queue.publish_event(
            event_type=EventType.HUMAN_VALIDATION_REQUESTED.name,
            payload=serialize_event(validation_event)
        )
    
    def _handle_task_assignment_events(self, event_type: str, payload: Dict[str, Any]):
        """
        Handle task assignment events.
        
        Args:
            event_type: Type of event
            payload: Event payload
        """
        try:
            if event_type == EventType.TASK_ASSIGNED.name:
                agent_id = payload.get("agent_id")
                if agent_id == "product_manager_pool":
                    task_id = payload.get("task_id")
                    logger.info(f"New task assigned to Product Manager: {task_id}")
                    # Optionally trigger an immediate poll
            
            elif event_type == EventType.TASK_UNASSIGNED.name:
                agent_id = payload.get("agent_id")
                if agent_id == "product_manager_pool":
                    task_id = payload.get("task_id")
                    logger.info(f"Task unassigned from Product Manager: {task_id}")
                    
                    # If we're currently processing this task, we could handle it here
                    with self.processing_lock:
                        if self.currently_processing_task == task_id:
                            logger.warning(f"Task {task_id} was unassigned while being processed")
                            # Could implement cancellation logic here
        
        except Exception as e:
            logger.error(f"Error handling task assignment event: {e}")
    
    def _find_highest_priority_task(self, tasks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the highest priority task from a list.
        
        Args:
            tasks: List of tasks
            
        Returns:
            The highest priority task, or None if list is empty
        """
        if not tasks:
            return None
        
        # Priority order (highest to lowest)
        priority_order = {
            "urgent": 0,
            "high": 1,
            "medium": 2,
            "low": 3
        }
        
        # Sort by priority then by creation time (oldest first)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                priority_order.get(t.get("priority", "medium"), 2),
                t.get("created_at", 0)
            )
        )
        
        return sorted_tasks[0] if sorted_tasks else None
    
    # Simulation methods for development/testing
    def _simulate_assigned_tasks_response(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Simulate a response to an assigned tasks query.
        
        Args:
            count: Number of tasks to generate
            
        Returns:
            A list of simulated tasks
        """
        tasks = []
        statuses = [TaskStatus.REQUEST_VALIDATION.value, TaskStatus.PRD_DEVELOPMENT.value]
        priorities = ["low", "medium", "high", "urgent"]
        
        for i in range(count):
            task_id = str(uuid.uuid4())
            tasks.append({
                "task_id": task_id,
                "title": f"Test task {i+1}",
                "status": statuses[i % len(statuses)],
                "priority": priorities[i % len(priorities)],
                "assigned_to": "product_manager_pool",
                "user_id": f"user_{i+1}",
                "created_at": time.time() - (3600 * (i+1)),  # Older tasks first
                "updated_at": time.time() - (1800 * (i+1))
            })
        
        return tasks
    
    def _simulate_product_manager_processing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Product Manager Agent processing a task.
        
        Args:
            task: The task to process
            
        Returns:
            Simulated processing result
        """
        # Simulate some processing time
        time.sleep(2)
        
        # Randomly decide if clarification is needed
        import random
        needs_clarification = random.random() < 0.3
        
        if needs_clarification:
            return {
                "needs_clarification": True,
                "clarification_questions": [
                    "What is the target audience for this feature?",
                    "What are the performance requirements?",
                    "Are there any regulatory concerns to address?"
                ]
            }
        else:
            return {
                "needs_clarification": False,
                "prd_data": {
                    "title": f"PRD for {task['title']}",
                    "description": "This is a simulated PRD document",
                    "requirements": [
                        {"id": "REQ-001", "description": "The system shall support user authentication"},
                        {"id": "REQ-002", "description": "The system shall provide data export capabilities"}
                    ],
                    "created_at": time.time(),
                    "created_by": "product_manager_agent"
                }
            }


def create_task_polling_service(message_queue: MessageQueue, product_manager_agent, poll_interval: int = 60) -> TaskPollingService:
    """
    Factory function to create a TaskPollingService.
    
    Args:
        message_queue: The message queue to use
        product_manager_agent: The agent responsible for processing tasks
        poll_interval: Time between polls in seconds
        
    Returns:
        A configured TaskPollingService instance
    """
    return TaskPollingService(message_queue, product_manager_agent, poll_interval) 