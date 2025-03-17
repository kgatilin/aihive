import json
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable, Optional, Type

import aio_pika
from aio_pika import Message, ExchangeType

from src.config import Config
from src.core.domain_events.base_event import DomainEvent
from src.core.message_broker.message_broker_interface import MessageBroker


logger = logging.getLogger(__name__)


class RabbitMQBroker(MessageBroker):
    """RabbitMQ implementation of the message broker interface."""
    
    def __init__(self):
        self.config = Config()
        self.connection = None
        self.channel = None
        self.event_exchange = None
        self.command_exchange = None
        self._event_consumers = []  # Keep track of consumers to cancel them later
    
    async def connect(self) -> None:
        """Connect to RabbitMQ and set up exchanges."""
        try:
            # Connect to RabbitMQ
            connection_uri = self.config.message_queue["connection_uri"]
            self.connection = await aio_pika.connect_robust(connection_uri)
            self.channel = await self.connection.channel()
            
            # Declare exchanges
            self.event_exchange = await self.channel.declare_exchange(
                self.config.message_queue["event_exchange"],
                ExchangeType.TOPIC,
                durable=True
            )
            
            self.command_exchange = await self.channel.declare_exchange(
                self.config.message_queue["command_exchange"],
                ExchangeType.DIRECT,
                durable=True
            )
            
            logger.info(f"Connected to RabbitMQ at {connection_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        try:
            # Cancel all consumers
            for consumer_tag in self._event_consumers:
                await self.channel.basic_cancel(consumer_tag)
            
            # Close connection
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {str(e)}")
    
    async def publish_event(self, event: DomainEvent) -> None:
        """Publish a domain event to the event exchange."""
        if not self.event_exchange:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            # Serialize the event to JSON
            event_data = event.to_dict()
            message = Message(
                body=json.dumps(event_data).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "version": event.version
                }
            )
            
            # Use event_type as routing key
            routing_key = event.event_type
            await self.event_exchange.publish(message, routing_key=routing_key)
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
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            # Create a queue with an optional name or auto-generated name
            queue = await self.channel.declare_queue(
                name=queue_name or "",
                durable=True,
                auto_delete=queue_name is None  # Auto-delete if no queue name provided
            )
            
            # Bind the queue to the exchange with the event type as routing key
            await queue.bind(self.event_exchange, routing_key=event_type)
            
            # Create a message handler
            async def message_handler(message):
                async with message.process():
                    try:
                        # Parse the message body
                        data = json.loads(message.body.decode())
                        
                        # Create the appropriate event object
                        if event_class:
                            event = event_class.from_dict(data)
                        else:
                            # Generic DomainEvent if no specific class provided
                            event = DomainEvent.from_dict(data)
                        
                        # Call the callback with the event
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Error processing event {event_type}: {str(e)}")
                        # Requeue the message if needed
                        # await message.reject(requeue=True)
            
            # Start consuming messages
            consumer_tag = await queue.consume(message_handler)
            self._event_consumers.append(consumer_tag)
            
            logger.info(f"Subscribed to event type: {event_type} with queue: {queue.name}")
        except Exception as e:
            logger.error(f"Failed to subscribe to event {event_type}: {str(e)}")
            raise
    
    async def publish_command(self, command_type: str, payload: Dict[str, Any]) -> None:
        """Publish a command to the command exchange."""
        if not self.command_exchange:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            message = Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                headers={
                    "command_type": command_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Use command_type as routing key
            await self.command_exchange.publish(message, routing_key=command_type)
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
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")
        
        try:
            # Create a queue with an optional name or auto-generated name
            queue = await self.channel.declare_queue(
                name=queue_name or "",
                durable=True,
                auto_delete=queue_name is None  # Auto-delete if no queue name provided
            )
            
            # Bind the queue to the exchange with the command type as routing key
            await queue.bind(self.command_exchange, routing_key=command_type)
            
            # Create a message handler
            async def message_handler(message):
                async with message.process():
                    try:
                        # Parse the message body
                        payload = json.loads(message.body.decode())
                        
                        # Call the callback with the payload
                        await callback(payload)
                    except Exception as e:
                        logger.error(f"Error processing command {command_type}: {str(e)}")
                        # Requeue the message if needed
                        # await message.reject(requeue=True)
            
            # Start consuming messages
            consumer_tag = await queue.consume(message_handler)
            self._event_consumers.append(consumer_tag)
            
            logger.info(f"Subscribed to command type: {command_type} with queue: {queue.name}")
        except Exception as e:
            logger.error(f"Failed to subscribe to command {command_type}: {str(e)}")
            raise 