"""
Message Queue Monitor Module

This module connects the message queue with the event monitoring system
to track events and commands flowing through the system.
"""

import logging
import json
from typing import Dict, Any, Optional, List
import uuid

from src.infrastructure.message_queue.message_queue import MessageQueue
from src.infrastructure.message_queue.event_monitor import EventMonitor
from src.infrastructure.message_queue.domain_events import EventType, CommandType, DomainEvent, DomainCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MessageQueueMonitor:
    """
    Connects a message queue to an event monitor.
    
    This class intercepts events and commands flowing through the message queue
    and forwards them to the event monitoring system for tracking and logging.
    """
    
    def __init__(self, message_queue: MessageQueue, event_monitor: EventMonitor):
        """
        Initialize the message queue monitor.
        
        Args:
            message_queue: The message queue to monitor
            event_monitor: The event monitoring system
        """
        self.message_queue = message_queue
        self.event_monitor = event_monitor
        self.original_publish_event = message_queue.publish_event
        self.original_publish_command = message_queue.publish_command
        
        # Monkey patch the message queue to intercept events and commands
        self.message_queue.publish_event = self._intercept_publish_event
        self.message_queue.publish_command = self._intercept_publish_command
        
        logger.info("Initialized MessageQueueMonitor")
    
    def _intercept_publish_event(self, event_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """
        Intercept event publication to monitor it.
        
        Args:
            event_type: Type of the event
            payload: Event data
            routing_key: Optional routing key for message routing
        """
        try:
            # Extract metadata from payload
            metadata = payload.get("metadata", {})
            event_id = metadata.get("event_id", str(uuid.uuid4()))
            correlation_id = metadata.get("correlation_id")
            source = metadata.get("source", "unknown")
            
            # Register the event with the monitor
            self.event_monitor.register_event(
                message_type=event_type,
                message_id=event_id,
                correlation_id=correlation_id,
                source=source,
                payload=payload
            )
            
            # Call the original publish method
            self.original_publish_event(event_type, payload, routing_key)
            
        except Exception as e:
            logger.error(f"Error intercepting event {event_type}: {e}")
            # Still publish the event even if monitoring fails
            self.original_publish_event(event_type, payload, routing_key)
    
    def _intercept_publish_command(self, command_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """
        Intercept command publication to monitor it.
        
        Args:
            command_type: Type of the command
            payload: Command data
            routing_key: Optional routing key for message routing
        """
        try:
            # Extract metadata from payload
            metadata = payload.get("metadata", {})
            command_id = metadata.get("command_id", str(uuid.uuid4()))
            correlation_id = metadata.get("correlation_id")
            source = metadata.get("source", "unknown")
            
            # Determine destination from routing key or payload
            destination = None
            if routing_key:
                parts = routing_key.split('.')
                if len(parts) > 1:
                    destination = parts[-1]
            
            if not destination:
                destination = payload.get("destination", "unknown")
            
            # Register the command with the monitor
            self.event_monitor.register_command(
                message_type=command_type,
                message_id=command_id,
                correlation_id=correlation_id,
                source=source,
                destination=destination,
                payload=payload
            )
            
            # Call the original publish method
            self.original_publish_command(command_type, payload, routing_key)
            
        except Exception as e:
            logger.error(f"Error intercepting command {command_type}: {e}")
            # Still publish the command even if monitoring fails
            self.original_publish_command(command_type, payload, routing_key)
    
    def restore_original_methods(self):
        """Restore the original message queue methods."""
        self.message_queue.publish_event = self.original_publish_event
        self.message_queue.publish_command = self.original_publish_command
        logger.info("Restored original message queue methods")


def connect_monitoring_system(message_queue: MessageQueue, event_monitor: EventMonitor) -> MessageQueueMonitor:
    """
    Connect a message queue to an event monitoring system.
    
    Args:
        message_queue: The message queue to monitor
        event_monitor: The event monitoring system
        
    Returns:
        The message queue monitor
    """
    return MessageQueueMonitor(message_queue, event_monitor) 