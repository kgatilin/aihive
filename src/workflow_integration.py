"""
Workflow Integration Module

This module combines all the components needed for the asynchronous workflow integration:
- Message Queue for asynchronous communication
- Task Scanning Service for periodic task scheduling
- Task Polling Service for agent task processing
- Error handling and recovery mechanisms
- Event monitoring and logging

This module serves as the main entry point for starting the workflow services.
"""

import logging
import os
import argparse
import threading
import time
import sys
from typing import Dict, Any, Optional, List

# Message Queue
from src.infrastructure.message_queue.message_queue import create_message_queue
from src.infrastructure.message_queue.domain_events import EventType, CommandType
from src.infrastructure.message_queue.error_handler import create_error_handler
from src.infrastructure.message_queue.event_monitor import create_event_monitoring_system
from src.infrastructure.message_queue.message_queue_monitor import connect_monitoring_system

# Orchestration Services
from src.orchestration.application.task_scanning_service import create_task_scanning_service

# Product Definition Services
from src.product_definition.application.task_polling_service import create_task_polling_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("workflow_integration.log")
    ]
)
logger = logging.getLogger(__name__)


class WorkflowIntegrationService:
    """
    Service to integrate and coordinate all asynchronous workflow components.
    
    This service initializes and connects all the components needed for
    asynchronous workflow processing, handling error recovery, monitoring,
    and logging.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the workflow integration service.
        
        Args:
            config: Configuration parameters
        """
        self.config = config
        self.running = False
        
        # Initialize components
        logger.info("Initializing workflow integration components")
        
        # Create message queue
        queue_type = config.get("message_queue_type", "in_memory")
        logger.info(f"Creating {queue_type} message queue")
        self.message_queue = create_message_queue(queue_type, **config.get("message_queue_config", {}))
        
        # Create error handler
        logger.info("Creating error handler")
        self.error_handler = create_error_handler(
            max_retries=config.get("max_retries", 3),
            initial_delay=config.get("retry_initial_delay", 1.0),
            max_delay=config.get("retry_max_delay", 60.0),
            backoff_factor=config.get("retry_backoff_factor", 2.0)
        )
        
        # Create event monitoring system
        logger.info("Creating event monitoring system")
        self.event_monitor = create_event_monitoring_system(
            log_directory=config.get("event_log_directory"),
            max_memory_entries=config.get("max_memory_log_entries", 1000),
            alert_threshold_seconds=config.get("alert_threshold_seconds", 60)
        )
        
        # Connect message queue to monitoring system
        logger.info("Connecting message queue to monitoring system")
        self.queue_monitor = connect_monitoring_system(self.message_queue, self.event_monitor)
        
        # Create task scanning service
        logger.info("Creating task scanning service")
        self.task_scanner = create_task_scanning_service(
            message_queue=self.message_queue,
            scan_interval=config.get("task_scan_interval", 300)
        )
        
        # Create product manager agent (placeholder for now)
        logger.info("Creating product manager agent")
        self.product_manager_agent = self._create_mock_product_manager()
        
        # Create task polling service
        logger.info("Creating task polling service")
        self.task_poller = create_task_polling_service(
            message_queue=self.message_queue,
            product_manager_agent=self.product_manager_agent,
            poll_interval=config.get("task_poll_interval", 60)
        )
        
        # Register stalled workflow alert handler
        self.event_monitor.register_alert_callback(self._handle_workflow_alert)
        
        logger.info("Workflow integration service initialized")
    
    def start(self):
        """Start all workflow services."""
        if self.running:
            logger.warning("Workflow integration service is already running")
            return
        
        logger.info("Starting workflow integration service")
        self.running = True
        
        # Start message queue first
        logger.info("Starting message queue")
        self.message_queue.start_consuming()
        
        # Start task scanner
        logger.info("Starting task scanning service")
        self.task_scanner.start()
        
        # Start task poller
        logger.info("Starting task polling service")
        self.task_poller.start()
        
        logger.info("All workflow services started")
        
        # Register shutdown handler
        def shutdown_handler():
            self.stop()
        
        # Register signal handlers if running in main thread
        if threading.current_thread() is threading.main_thread():
            import signal
            signal.signal(signal.SIGINT, lambda sig, frame: shutdown_handler())
            signal.signal(signal.SIGTERM, lambda sig, frame: shutdown_handler())
    
    def stop(self):
        """Stop all workflow services."""
        if not self.running:
            logger.warning("Workflow integration service is not running")
            return
        
        logger.info("Stopping workflow integration service")
        self.running = False
        
        # Stop in reverse order of startup
        
        # Stop task poller
        logger.info("Stopping task polling service")
        self.task_poller.stop()
        
        # Stop task scanner
        logger.info("Stopping task scanning service")
        self.task_scanner.stop()
        
        # Stop event monitor
        logger.info("Stopping event monitoring system")
        self.event_monitor.stop()
        
        # Stop message queue
        logger.info("Stopping message queue")
        self.message_queue.stop_consuming()
        self.message_queue.close()
        
        # Restore original message queue methods
        self.queue_monitor.restore_original_methods()
        
        logger.info("All workflow services stopped")
    
    def _handle_workflow_alert(self, alert_data: Dict[str, Any]):
        """
        Handle workflow alerts from the event monitor.
        
        Args:
            alert_data: Alert information
        """
        alert_type = alert_data.get("type")
        
        if alert_type == "stalled_workflow":
            correlation_id = alert_data.get("correlation_id")
            logger.warning(f"Stalled workflow detected: {correlation_id}")
            
            # Retrieve workflow status for more detailed diagnostics
            workflow_status = self.event_monitor.get_workflow_status(correlation_id)
            if workflow_status:
                events = workflow_status.get("events", [])
                commands = workflow_status.get("commands", [])
                
                if events:
                    last_event = events[-1]
                    logger.warning(f"Last event: {last_event.get('message_type')} from {last_event.get('source')}")
                
                if commands:
                    last_command = commands[-1]
                    logger.warning(f"Last command: {last_command.get('message_type')} from {last_command.get('source')}")
                
                # Could implement recovery actions here
    
    def _create_mock_product_manager(self):
        """
        Create a mock product manager agent for testing.
        
        In a real implementation, this would be a properly instantiated agent.
        
        Returns:
            A mock product manager agent
        """
        # For now, just return a placeholder object
        # This will be replaced by a real agent in a production implementation
        class MockProductManager:
            def process_task(self, task):
                logger.info(f"Mock Product Manager processing task: {task.get('task_id')}")
                time.sleep(2)  # Simulate processing time
                
                # Randomly decide if clarification is needed (for testing)
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
                            "title": f"PRD for task {task.get('task_id')}",
                            "description": "This is a mock PRD document",
                            "requirements": [
                                {"id": "REQ-001", "description": "User authentication"},
                                {"id": "REQ-002", "description": "Data export"}
                            ]
                        }
                    }
        
        return MockProductManager()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start the workflow integration service")
    
    parser.add_argument(
        "--message-queue-type",
        choices=["in_memory", "rabbitmq"],
        default="in_memory",
        help="Type of message queue to use (default: in_memory)"
    )
    
    parser.add_argument(
        "--scan-interval",
        type=int,
        default=300,
        help="Interval in seconds between task scans (default: 300)"
    )
    
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Interval in seconds between task polls (default: 60)"
    )
    
    parser.add_argument(
        "--log-directory",
        default="logs",
        help="Directory for storing event logs (default: logs)"
    )
    
    return parser.parse_args()


def create_config_from_args(args):
    """Create configuration from command line arguments."""
    config = {
        "message_queue_type": args.message_queue_type,
        "task_scan_interval": args.scan_interval,
        "task_poll_interval": args.poll_interval,
        "event_log_directory": args.log_directory,
        "message_queue_config": {}
    }
    
    # If using RabbitMQ, read connection parameters from environment variables
    if args.message_queue_type == "rabbitmq":
        config["message_queue_config"] = {
            "host": os.environ.get("RABBITMQ_HOST", "localhost"),
            "port": int(os.environ.get("RABBITMQ_PORT", "5672")),
            "username": os.environ.get("RABBITMQ_USERNAME", "guest"),
            "password": os.environ.get("RABBITMQ_PASSWORD", "guest")
        }
    
    return config


def main():
    """Main entry point for workflow integration service."""
    args = parse_args()
    config = create_config_from_args(args)
    
    service = WorkflowIntegrationService(config)
    
    try:
        logger.info("Starting workflow integration service")
        service.start()
        
        # Keep main thread alive
        while service.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Error in workflow integration service: {e}")
    finally:
        service.stop()
        logger.info("Workflow integration service shutdown complete")


if __name__ == "__main__":
    main() 