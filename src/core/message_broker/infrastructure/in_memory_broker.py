import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable, Optional, Type, List

from src.core.domain_events.base_event import DomainEvent
from src.core.message_broker.message_broker_interface import MessageBroker

logger = logging.getLogger(__name__)

class InMemoryBroker(MessageBroker):
    """In-memory implementation of the message broker interface."""
    
    def __init__(self):
        self.event_subscribers: Dict[str, List[Callable[[DomainEvent], Awaitable[None]]]] = {}
        self.command_subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.is_connected = False
    
    async def connect(self) -> None:
        """Connect to the in-memory broker (no-op)."""
        self.is_connected = True
        logger.info("Connected to in-memory message broker")
    
    async def disconnect(self) -> None:
        """Disconnect from the in-memory broker (no-op)."""
        self.is_connected = False
        logger.info("Disconnected from in-memory message broker")
    
    async def publish_event(self, event: DomainEvent) -> None:
        """Publish a domain event to in-memory subscribers."""
        if not self.is_connected:
            raise RuntimeError("Not connected to in-memory broker")
        
        try:
            event_type = event.event_type
            if event_type in self.event_subscribers:
                # Create tasks for all subscribers
                tasks = []
                for callback in self.event_subscribers[event_type]:
                    task = asyncio.create_task(callback(event))
                    tasks.append(task)
                
                # Wait for all subscribers to process the event
                if tasks:
                    await asyncio.gather(*tasks)
                
            logger.debug(f"Published event {event.event_type} with ID {event.event_id}")
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {str(e)}")
            raise
    
    async def subscribe_to_event(
        self, 
        event_type: str, 
        callback: Callable[[DomainEvent], Awaitable[None]],
        queue_name: Optional[str] = None,
        event_class: Optional[Type[DomainEvent]] = None
    ) -> None:
        """Subscribe to a specific event type with a callback function."""
        if not self.is_connected:
            raise RuntimeError("Not connected to in-memory broker")
        
        try:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            
            self.event_subscribers[event_type].append(callback)
            logger.info(f"Subscribed to event type: {event_type}")
        except Exception as e:
            logger.error(f"Failed to subscribe to event {event_type}: {str(e)}")
            raise
    
    async def publish_command(self, command_type: str, payload: Dict[str, Any]) -> None:
        """Publish a command to in-memory subscribers."""
        if not self.is_connected:
            raise RuntimeError("Not connected to in-memory broker")
        
        try:
            if command_type in self.command_subscribers:
                # Create tasks for all subscribers
                tasks = []
                for callback in self.command_subscribers[command_type]:
                    task = asyncio.create_task(callback(payload))
                    tasks.append(task)
                
                # Wait for all subscribers to process the command
                if tasks:
                    await asyncio.gather(*tasks)
                
            logger.debug(f"Published command {command_type}")
        except Exception as e:
            logger.error(f"Failed to publish command {command_type}: {str(e)}")
            raise
    
    async def subscribe_to_command(
        self,
        command_type: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        queue_name: Optional[str] = None
    ) -> None:
        """Subscribe to a specific command type with a callback function."""
        if not self.is_connected:
            raise RuntimeError("Not connected to in-memory broker")
        
        try:
            if command_type not in self.command_subscribers:
                self.command_subscribers[command_type] = []
            
            self.command_subscribers[command_type].append(callback)
            logger.info(f"Subscribed to command type: {command_type}")
        except Exception as e:
            logger.error(f"Failed to subscribe to command {command_type}: {str(e)}")
            raise 