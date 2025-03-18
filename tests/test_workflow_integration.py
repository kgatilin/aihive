"""
Unit tests for workflow integration module.

These tests verify that the workflow integration components connect properly and
function correctly together.
"""

import unittest
import threading
import time
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

from src.workflow_integration import WorkflowIntegrationService
from src.infrastructure.message_queue.domain_events import EventType, CommandType


class TestWorkflowIntegration(unittest.TestCase):
    """Test cases for workflow integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config = {
            "message_queue_type": "in_memory",
            "task_scan_interval": 5,  # Short interval for testing
            "task_poll_interval": 2,  # Short interval for testing
            "event_log_directory": self.temp_dir,
            "max_memory_log_entries": 100,
            "alert_threshold_seconds": 10,
            "message_queue_config": {}
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_service_initialization(self):
        """Test that the service initializes all components correctly."""
        service = WorkflowIntegrationService(self.config)
        
        # Verify all components were created
        self.assertIsNotNone(service.message_queue)
        self.assertIsNotNone(service.error_handler)
        self.assertIsNotNone(service.event_monitor)
        self.assertIsNotNone(service.queue_monitor)
        self.assertIsNotNone(service.task_scanner)
        self.assertIsNotNone(service.task_poller)
        self.assertIsNotNone(service.product_manager_agent)
        
        # Verify service state
        self.assertFalse(service.running)
    
    def test_service_start_stop(self):
        """Test starting and stopping the service."""
        service = WorkflowIntegrationService(self.config)
        
        # Mock component methods to verify calls
        service.message_queue.start_consuming = MagicMock()
        service.message_queue.stop_consuming = MagicMock()
        service.message_queue.close = MagicMock()
        service.task_scanner.start = MagicMock()
        service.task_scanner.stop = MagicMock()
        service.task_poller.start = MagicMock()
        service.task_poller.stop = MagicMock()
        service.event_monitor.stop = MagicMock()
        service.queue_monitor.restore_original_methods = MagicMock()
        
        # Start service
        service.start()
        
        # Verify components were started
        service.message_queue.start_consuming.assert_called_once()
        service.task_scanner.start.assert_called_once()
        service.task_poller.start.assert_called_once()
        self.assertTrue(service.running)
        
        # Stop service
        service.stop()
        
        # Verify components were stopped
        service.task_poller.stop.assert_called_once()
        service.task_scanner.stop.assert_called_once()
        service.event_monitor.stop.assert_called_once()
        service.message_queue.stop_consuming.assert_called_once()
        service.message_queue.close.assert_called_once()
        service.queue_monitor.restore_original_methods.assert_called_once()
        self.assertFalse(service.running)
    
    def test_event_flow(self):
        """Test event flow through the integrated system."""
        service = WorkflowIntegrationService(self.config)
        
        # Set up mocks
        original_publish_event = service.message_queue.publish_event
        service.message_queue.publish_event = MagicMock(side_effect=original_publish_event)
        
        # Start service in a separate thread
        thread = threading.Thread(target=service.start)
        thread.daemon = True
        thread.start()
        
        try:
            # Wait for service to start
            time.sleep(0.5)
            self.assertTrue(service.running)
            
            # Simulate a user request event
            event_payload = {
                "metadata": {
                    "event_id": "test-event-001",
                    "correlation_id": "test-workflow-001",
                    "source": "test_client"
                },
                "payload": {
                    "user_id": "test_user",
                    "request_type": "feature_request",
                    "request_data": {
                        "title": "Test Feature",
                        "description": "A test feature for unit testing"
                    }
                }
            }
            
            # Publish the event
            service.message_queue.publish_event(
                event_type=EventType.USER_REQUEST_SUBMITTED.name,
                payload=event_payload
            )
            
            # Wait for event to be processed
            time.sleep(1)
            
            # Verify event was registered in monitoring system
            workflows = service.event_monitor.get_active_workflows()
            self.assertIn("test-workflow-001", workflows)
            
            # Verify workflow contains our event
            workflow = workflows["test-workflow-001"]
            events = workflow.get("events", [])
            self.assertTrue(len(events) >= 1)
            
            event = events[0]
            self.assertEqual(event["message_type"], EventType.USER_REQUEST_SUBMITTED.name)
            self.assertEqual(event["source"], "test_client")
            
        finally:
            # Stop service
            service.stop()
            thread.join(timeout=5)
    
    def test_stalled_workflow_alert(self):
        """Test that stalled workflow alerts are triggered."""
        # Override threshold to make testing faster
        self.config["alert_threshold_seconds"] = 2
        service = WorkflowIntegrationService(self.config)
        
        # Set up mock alert handler
        alert_handler = MagicMock()
        service.event_monitor.register_alert_callback(alert_handler)
        
        # Start service
        service.start()
        
        try:
            # Create a workflow without completing it
            correlation_id = "test-stalled-workflow"
            event_payload = {
                "metadata": {
                    "event_id": "test-event-002",
                    "correlation_id": correlation_id,
                    "source": "test_client"
                },
                "payload": {
                    "user_id": "test_user",
                    "request_type": "feature_request"
                }
            }
            
            # Register event directly with monitor
            service.event_monitor.register_event(
                message_type=EventType.USER_REQUEST_SUBMITTED.name,
                message_id="test-event-002",
                correlation_id=correlation_id,
                source="test_client",
                payload=event_payload["payload"]
            )
            
            # Wait for alert to be triggered
            time.sleep(4)  # Slightly longer than threshold
            
            # Verify alert was called
            alert_handler.assert_called()
            alert_data = alert_handler.call_args[0][0]
            self.assertEqual(alert_data["type"], "stalled_workflow")
            self.assertEqual(alert_data["correlation_id"], correlation_id)
            
        finally:
            # Stop service
            service.stop()
    
    @patch('src.workflow_integration.create_task_scanning_service')
    def test_task_scanner_creation(self, mock_create_scanner):
        """Test that task scanner is created with correct parameters."""
        # Create mock scanner
        mock_scanner = MagicMock()
        mock_create_scanner.return_value = mock_scanner
        
        # Create service
        service = WorkflowIntegrationService(self.config)
        
        # Verify scanner was created with correct parameters
        mock_create_scanner.assert_called_once()
        args, kwargs = mock_create_scanner.call_args
        self.assertEqual(kwargs["scan_interval"], self.config["task_scan_interval"])
        self.assertIs(kwargs["message_queue"], service.message_queue)
    
    @patch('src.workflow_integration.create_task_polling_service')
    def test_task_poller_creation(self, mock_create_poller):
        """Test that task poller is created with correct parameters."""
        # Create mock poller
        mock_poller = MagicMock()
        mock_create_poller.return_value = mock_poller
        
        # Create service
        service = WorkflowIntegrationService(self.config)
        
        # Verify poller was created with correct parameters
        mock_create_poller.assert_called_once()
        args, kwargs = mock_create_poller.call_args
        self.assertEqual(kwargs["poll_interval"], self.config["task_poll_interval"])
        self.assertIs(kwargs["message_queue"], service.message_queue)
        self.assertIs(kwargs["product_manager_agent"], service.product_manager_agent)


if __name__ == '__main__':
    unittest.main() 