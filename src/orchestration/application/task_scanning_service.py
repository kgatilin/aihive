"""
Task Scanning Service Module

This module implements the Task Scanning Service, which periodically scans
for tasks needing processing and coordinates workflow state transitions.
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable
import uuid

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


class TaskScanningService:
    """
    Service responsible for periodically scanning tasks and coordinating workflow.
    
    This service runs in the background and periodically scans the task repository
    for tasks that need processing, triggering appropriate state transitions and
    command publishing.
    """
    
    def __init__(self, message_queue: MessageQueue, scan_interval: int = 300):
        """
        Initialize the Task Scanning Service.
        
        Args:
            message_queue: The message queue for publishing events and commands
            scan_interval: Time between scans in seconds (default: 300 seconds / 5 minutes)
        """
        self.message_queue = message_queue
        self.scan_interval = scan_interval
        self.running = False
        self.scan_thread = None
        self.source_id = f"task_scanner_{uuid.uuid4()}"
        
        logger.info(f"Initialized TaskScanningService with scan interval: {scan_interval}s")
        
        # Register event handlers
        self.message_queue.subscribe_to_events(
            [EventType.TASK_CREATED.name, EventType.TASK_STATUS_CHANGED.name], 
            self._handle_task_events
        )
    
    def start(self):
        """Start the periodic task scanning."""
        if self.running:
            logger.warning("Task scanning service is already running")
            return
        
        self.running = True
        self.scan_thread = threading.Thread(target=self._scanning_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        logger.info("Started task scanning service")
    
    def stop(self):
        """Stop the periodic task scanning."""
        if not self.running:
            logger.warning("Task scanning service is not running")
            return
        
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=10)
        
        logger.info("Stopped task scanning service")
    
    def _scanning_loop(self):
        """Background thread for periodic task scanning."""
        while self.running:
            try:
                self._perform_scan()
            except Exception as e:
                logger.error(f"Error during task scan: {e}")
            
            # Sleep until next scan
            time.sleep(self.scan_interval)
    
    def _perform_scan(self):
        """Perform a single scan of tasks."""
        logger.info("Starting task scan")
        
        # Publish scan initiated event
        scan_id = str(uuid.uuid4())
        scan_init_event = create_event(
            event_type=EventType.TASK_SCAN_INITIATED,
            payload={"scan_id": scan_id, "timestamp": time.time()},
            source=self.source_id
        )
        self.message_queue.publish_event(
            event_type=EventType.TASK_SCAN_INITIATED.name,
            payload=serialize_event(scan_init_event)
        )
        
        # Scan for new tasks
        self._scan_new_tasks(scan_id)
        
        # Scan for clarification needed tasks
        self._scan_clarification_needed_tasks(scan_id)
        
        # Scan for PRD validation tasks
        self._scan_prd_validation_tasks(scan_id)
        
        # Publish scan completed event
        scan_complete_event = create_event(
            event_type=EventType.TASK_SCAN_COMPLETED,
            payload={"scan_id": scan_id, "timestamp": time.time()},
            source=self.source_id,
            correlation_id=scan_id
        )
        self.message_queue.publish_event(
            event_type=EventType.TASK_SCAN_COMPLETED.name,
            payload=serialize_event(scan_complete_event)
        )
        
        logger.info(f"Completed task scan with ID: {scan_id}")
    
    def _scan_new_tasks(self, scan_id: str):
        """
        Scan for tasks in NEW status and transition them.
        
        Args:
            scan_id: The ID of the current scan operation
        """
        # Publish command to query NEW tasks
        query_cmd = create_command(
            command_type=CommandType.QUERY_TASKS,
            payload={"status": TaskStatus.NEW.value},
            source=self.source_id,
            correlation_id=scan_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.QUERY_TASKS.name,
            payload=serialize_command(query_cmd)
        )
        
        # This would typically have a callback, but for now we'll simulate the response
        # In a real implementation, this would be handled by an event handler
        
        # For demonstration, let's assume we received a response with some tasks
        # In reality, this would come from the event handler
        tasks = self._simulate_task_query_response(TaskStatus.NEW)
        
        logger.info(f"Found {len(tasks)} tasks in NEW status")
        
        for task in tasks:
            # Update task status to REQUEST_VALIDATION
            status_cmd = create_command(
                command_type=CommandType.UPDATE_TASK_STATUS,
                payload={
                    "task_id": task["task_id"],
                    "new_status": TaskStatus.REQUEST_VALIDATION.value,
                    "comment": "Task status updated by Task Scanner"
                },
                source=self.source_id,
                correlation_id=scan_id
            )
            self.message_queue.publish_command(
                command_type=CommandType.UPDATE_TASK_STATUS.name,
                payload=serialize_command(status_cmd)
            )
            
            # Assign task to Product Manager agent pool
            assign_cmd = create_command(
                command_type=CommandType.ASSIGN_TASK,
                payload={
                    "task_id": task["task_id"],
                    "agent_id": "product_manager_pool",
                    "assignment_reason": "Initial requirements analysis"
                },
                source=self.source_id,
                correlation_id=scan_id
            )
            self.message_queue.publish_command(
                command_type=CommandType.ASSIGN_TASK.name,
                payload=serialize_command(assign_cmd)
            )
            
            logger.info(f"Processed NEW task: {task['task_id']}")
    
    def _scan_clarification_needed_tasks(self, scan_id: str):
        """
        Scan for tasks in CLARIFICATION_NEEDED status.
        
        Args:
            scan_id: The ID of the current scan operation
        """
        # Publish command to query CLARIFICATION_NEEDED tasks
        query_cmd = create_command(
            command_type=CommandType.QUERY_TASKS,
            payload={"status": TaskStatus.CLARIFICATION_NEEDED.value},
            source=self.source_id,
            correlation_id=scan_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.QUERY_TASKS.name,
            payload=serialize_command(query_cmd)
        )
        
        # Simulate query response
        tasks = self._simulate_task_query_response(TaskStatus.CLARIFICATION_NEEDED)
        
        logger.info(f"Found {len(tasks)} tasks needing clarification")
        
        for task in tasks:
            # Check if notification was already sent (would be in task data in real impl)
            if not task.get("notification_sent", False):
                # Send notification to user
                notify_cmd = create_command(
                    command_type=CommandType.SEND_NOTIFICATION,
                    payload={
                        "user_id": task["user_id"],
                        "task_id": task["task_id"],
                        "notification_type": "CLARIFICATION_REQUESTED",
                        "notification_content": {
                            "task_title": task["title"],
                            "clarification_questions": task.get("clarification_questions", [])
                        }
                    },
                    source=self.source_id,
                    correlation_id=scan_id
                )
                self.message_queue.publish_command(
                    command_type=CommandType.SEND_NOTIFICATION.name,
                    payload=serialize_command(notify_cmd)
                )
                
                # Update task to mark notification as sent (in a real system)
                # For now, just log it
                logger.info(f"Sent clarification notification for task: {task['task_id']}")
    
    def _scan_prd_validation_tasks(self, scan_id: str):
        """
        Scan for tasks in PRD_VALIDATION status.
        
        Args:
            scan_id: The ID of the current scan operation
        """
        # Publish command to query PRD_VALIDATION tasks
        query_cmd = create_command(
            command_type=CommandType.QUERY_TASKS,
            payload={"status": TaskStatus.PRD_VALIDATION.value},
            source=self.source_id,
            correlation_id=scan_id
        )
        self.message_queue.publish_command(
            command_type=CommandType.QUERY_TASKS.name,
            payload=serialize_command(query_cmd)
        )
        
        # Simulate query response
        tasks = self._simulate_task_query_response(TaskStatus.PRD_VALIDATION)
        
        logger.info(f"Found {len(tasks)} tasks awaiting PRD validation")
        
        for task in tasks:
            # Check if notification was already sent (would be in task data in real impl)
            if not task.get("validation_notification_sent", False):
                # Send notification to user
                notify_cmd = create_command(
                    command_type=CommandType.SEND_NOTIFICATION,
                    payload={
                        "user_id": task["user_id"],
                        "task_id": task["task_id"],
                        "notification_type": "PRD_VALIDATION_REQUESTED",
                        "notification_content": {
                            "task_title": task["title"],
                            "prd_link": task.get("prd_link", ""),
                            "validation_instructions": "Please review and approve or reject this PRD"
                        }
                    },
                    source=self.source_id,
                    correlation_id=scan_id
                )
                self.message_queue.publish_command(
                    command_type=CommandType.SEND_NOTIFICATION.name,
                    payload=serialize_command(notify_cmd)
                )
                
                # Update task to mark validation notification as sent (in a real system)
                # For now, just log it
                logger.info(f"Sent PRD validation notification for task: {task['task_id']}")
    
    def _handle_task_events(self, event_type: str, payload: Dict[str, Any]):
        """
        Handle task-related events.
        
        Args:
            event_type: The type of event
            payload: The event payload
        """
        try:
            # Log the event
            logger.info(f"Received task event: {event_type}")
            
            # Handle specific events here
            # This could include triggering immediate actions rather than waiting for the next scan
            
            if event_type == EventType.TASK_CREATED.name:
                # Optionally trigger an immediate scan for new tasks
                pass
            
            elif event_type == EventType.TASK_STATUS_CHANGED.name:
                # React to status changes that might need immediate attention
                new_status = payload.get("new_status")
                
                if new_status == TaskStatus.CLARIFICATION_NEEDED.value:
                    # Could trigger immediate notification
                    task_id = payload.get("task_id")
                    logger.info(f"Task {task_id} needs clarification - will be processed in next scan")
                
                elif new_status == TaskStatus.PRD_VALIDATION.value:
                    # Could trigger immediate notification
                    task_id = payload.get("task_id")
                    logger.info(f"Task {task_id} PRD ready for validation - will be processed in next scan")
            
        except Exception as e:
            logger.error(f"Error handling task event: {e}")
    
    # This is a simulation method for development/testing
    def _simulate_task_query_response(self, status: TaskStatus, count: int = 3) -> List[Dict[str, Any]]:
        """
        Simulate a response to a task query for testing.
        
        In a real implementation, this would be handled by an event handler.
        
        Args:
            status: The status of tasks to simulate
            count: How many tasks to generate
            
        Returns:
            A list of simulated tasks
        """
        tasks = []
        for i in range(count):
            task_id = str(uuid.uuid4())
            task = {
                "task_id": task_id,
                "title": f"Task {i+1} in {status.value} status",
                "status": status.value,
                "priority": "medium",
                "user_id": f"user_{i+1}",
                "created_at": time.time() - 3600,  # 1 hour ago
                "updated_at": time.time() - 1800,  # 30 minutes ago
            }
            
            # Add status-specific data
            if status == TaskStatus.CLARIFICATION_NEEDED:
                task["clarification_questions"] = [
                    "What is the target audience?",
                    "What is the expected timeline?"
                ]
            
            if status == TaskStatus.PRD_VALIDATION:
                task["prd_link"] = f"/product_requirements/{task_id}"
            
            tasks.append(task)
        
        return tasks


def create_task_scanning_service(message_queue: MessageQueue, scan_interval: int = 300) -> TaskScanningService:
    """
    Factory function to create a TaskScanningService.
    
    Args:
        message_queue: The message queue to use
        scan_interval: Time between scans in seconds
        
    Returns:
        A configured TaskScanningService instance
    """
    return TaskScanningService(message_queue, scan_interval) 