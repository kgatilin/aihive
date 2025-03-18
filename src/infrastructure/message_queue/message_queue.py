from abc import ABC, abstractmethod
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageQueue(ABC):
    """Abstract base class for message queue implementations."""
    
    @abstractmethod
    def publish_event(self, event_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """
        Publish an event to the message queue.
        
        Args:
            event_type: Type of the event
            payload: Event data
            routing_key: Optional routing key for message routing
        """
        pass
    
    @abstractmethod
    def publish_command(self, command_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """
        Publish a command to the message queue.
        
        Args:
            command_type: Type of the command
            payload: Command data
            routing_key: Optional routing key for message routing
        """
        pass
    
    @abstractmethod
    def subscribe_to_events(self, event_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Subscribe to events of specified types.
        
        Args:
            event_types: List of event types to subscribe to
            callback: Function to call when an event is received
        """
        pass
    
    @abstractmethod
    def subscribe_to_commands(self, command_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Subscribe to commands of specified types.
        
        Args:
            command_types: List of command types to subscribe to
            callback: Function to call when a command is received
        """
        pass
    
    @abstractmethod
    def start_consuming(self) -> None:
        """Start consuming messages from the queue."""
        pass
    
    @abstractmethod
    def stop_consuming(self) -> None:
        """Stop consuming messages from the queue."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close connection to the message queue."""
        pass


class InMemoryMessageQueue(MessageQueue):
    """In-memory implementation of message queue for testing and development."""
    
    def __init__(self):
        self.event_subscribers: Dict[str, List[Callable]] = {}
        self.command_subscribers: Dict[str, List[Callable]] = {}
        self.is_consuming = False
        logger.info("Initialized InMemoryMessageQueue")
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """Publish an event to in-memory subscribers."""
        logger.info(f"Publishing event: {event_type} with payload: {payload}")
        if event_type in self.event_subscribers:
            for callback in self.event_subscribers[event_type]:
                try:
                    callback(event_type, payload)
                except Exception as e:
                    logger.error(f"Error in event subscriber for {event_type}: {e}")
    
    def publish_command(self, command_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """Publish a command to in-memory subscribers."""
        logger.info(f"Publishing command: {command_type} with payload: {payload}")
        if command_type in self.command_subscribers:
            for callback in self.command_subscribers[command_type]:
                try:
                    callback(command_type, payload)
                except Exception as e:
                    logger.error(f"Error in command subscriber for {command_type}: {e}")
    
    def subscribe_to_events(self, event_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to events of specified types."""
        for event_type in event_types:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            self.event_subscribers[event_type].append(callback)
            logger.info(f"Subscribed to event: {event_type}")
    
    def subscribe_to_commands(self, command_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to commands of specified types."""
        for command_type in command_types:
            if command_type not in self.command_subscribers:
                self.command_subscribers[command_type] = []
            self.command_subscribers[command_type].append(callback)
            logger.info(f"Subscribed to command: {command_type}")
    
    def start_consuming(self) -> None:
        """Start consuming messages (no-op for in-memory queue)."""
        logger.info("Started consuming messages from in-memory queue")
        self.is_consuming = True
    
    def stop_consuming(self) -> None:
        """Stop consuming messages (no-op for in-memory queue)."""
        logger.info("Stopped consuming messages from in-memory queue")
        self.is_consuming = False
    
    def close(self) -> None:
        """Close connection (no-op for in-memory queue)."""
        logger.info("Closed in-memory queue")
        self.is_consuming = False
        self.event_subscribers = {}
        self.command_subscribers = {}


class RabbitMQMessageQueue(MessageQueue):
    """RabbitMQ implementation of message queue."""
    
    def __init__(self, host: str, port: int, username: str, password: str, 
                 exchange_name: str = 'aihive_exchange', event_queue: str = 'event_queue', 
                 command_queue: str = 'command_queue'):
        """
        Initialize RabbitMQ connection.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: RabbitMQ username
            password: RabbitMQ password
            exchange_name: Name of the exchange to use
            event_queue: Name of the event queue
            command_queue: Name of the command queue
        """
        try:
            import pika
            
            self.host = host
            self.port = port
            self.username = username
            self.password = password
            self.exchange_name = exchange_name
            self.event_queue = event_queue
            self.command_queue = command_queue
            
            # Create connection parameters
            credentials = pika.PlainCredentials(username, password)
            self.connection_params = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Connect to RabbitMQ
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queues
            self.channel.queue_declare(queue=event_queue, durable=True)
            self.channel.queue_declare(queue=command_queue, durable=True)
            
            # Event subscribers
            self.event_callbacks: Dict[str, List[Callable]] = {}
            
            # Command subscribers
            self.command_callbacks: Dict[str, List[Callable]] = {}
            
            # Consumer tag for later cancellation
            self.consumer_tag = None
            
            logger.info(f"Connected to RabbitMQ on {host}:{port}")
            
        except ImportError:
            logger.error("pika module not installed. Cannot use RabbitMQMessageQueue.")
            raise
        except Exception as e:
            logger.error(f"Error initializing RabbitMQ connection: {e}")
            raise
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """Publish an event to RabbitMQ."""
        try:
            import pika
            
            if not routing_key:
                routing_key = f"event.{event_type}"
            
            message = {
                "type": event_type,
                "payload": payload
            }
            
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published event: {event_type} with routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}")
            self._reconnect_if_needed()
    
    def publish_command(self, command_type: str, payload: Dict[str, Any], routing_key: Optional[str] = None) -> None:
        """Publish a command to RabbitMQ."""
        try:
            import pika
            
            if not routing_key:
                routing_key = f"command.{command_type}"
            
            message = {
                "type": command_type,
                "payload": payload
            }
            
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published command: {command_type} with routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Error publishing command {command_type}: {e}")
            self._reconnect_if_needed()
    
    def subscribe_to_events(self, event_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to events of specified types."""
        try:
            # Bind queue to exchange with routing patterns for each event type
            for event_type in event_types:
                routing_key = f"event.{event_type}"
                self.channel.queue_bind(
                    exchange=self.exchange_name,
                    queue=self.event_queue,
                    routing_key=routing_key
                )
                
                if event_type not in self.event_callbacks:
                    self.event_callbacks[event_type] = []
                self.event_callbacks[event_type].append(callback)
                
                logger.info(f"Subscribed to event: {event_type} with routing key: {routing_key}")
                
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
            self._reconnect_if_needed()
    
    def subscribe_to_commands(self, command_types: List[str], callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Subscribe to commands of specified types."""
        try:
            # Bind queue to exchange with routing patterns for each command type
            for command_type in command_types:
                routing_key = f"command.{command_type}"
                self.channel.queue_bind(
                    exchange=self.exchange_name,
                    queue=self.command_queue,
                    routing_key=routing_key
                )
                
                if command_type not in self.command_callbacks:
                    self.command_callbacks[command_type] = []
                self.command_callbacks[command_type].append(callback)
                
                logger.info(f"Subscribed to command: {command_type} with routing key: {routing_key}")
                
        except Exception as e:
            logger.error(f"Error subscribing to commands: {e}")
            self._reconnect_if_needed()
    
    def _event_callback(self, ch, method, properties, body):
        """Callback function for event queue."""
        try:
            message = json.loads(body)
            event_type = message.get("type")
            payload = message.get("payload", {})
            
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        callback(event_type, payload)
                    except Exception as e:
                        logger.error(f"Error in event callback for {event_type}: {e}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message: {body}")
            # Negative acknowledgement for bad message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing event message: {e}")
            # Negative acknowledgement with requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _command_callback(self, ch, method, properties, body):
        """Callback function for command queue."""
        try:
            message = json.loads(body)
            command_type = message.get("type")
            payload = message.get("payload", {})
            
            if command_type in self.command_callbacks:
                for callback in self.command_callbacks[command_type]:
                    try:
                        callback(command_type, payload)
                    except Exception as e:
                        logger.error(f"Error in command callback for {command_type}: {e}")
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to decode message: {body}")
            # Negative acknowledgement for bad message
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing command message: {e}")
            # Negative acknowledgement with requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self) -> None:
        """Start consuming messages from queues."""
        try:
            # Start consuming from event queue
            self.event_consumer_tag = self.channel.basic_consume(
                queue=self.event_queue,
                on_message_callback=self._event_callback
            )
            
            # Start consuming from command queue
            self.command_consumer_tag = self.channel.basic_consume(
                queue=self.command_queue,
                on_message_callback=self._command_callback
            )
            
            logger.info("Started consuming messages from RabbitMQ queues")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Error starting to consume messages: {e}")
            self._reconnect_if_needed()
    
    def stop_consuming(self) -> None:
        """Stop consuming messages from queues."""
        try:
            if self.event_consumer_tag:
                self.channel.basic_cancel(self.event_consumer_tag)
            
            if self.command_consumer_tag:
                self.channel.basic_cancel(self.command_consumer_tag)
            
            logger.info("Stopped consuming messages from RabbitMQ queues")
            
        except Exception as e:
            logger.error(f"Error stopping consumption: {e}")
    
    def close(self) -> None:
        """Close connection to RabbitMQ."""
        try:
            self.stop_consuming()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("Closed RabbitMQ connection")
            
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    def _reconnect_if_needed(self) -> None:
        """Reconnect to RabbitMQ if connection is closed."""
        import pika
        
        try:
            if not self.connection or not self.connection.is_open:
                logger.info("Reconnecting to RabbitMQ...")
                self.connection = pika.BlockingConnection(self.connection_params)
                self.channel = self.connection.channel()
                
                # Redeclare exchange and queues
                self.channel.exchange_declare(
                    exchange=self.exchange_name,
                    exchange_type='topic',
                    durable=True
                )
                
                self.channel.queue_declare(queue=self.event_queue, durable=True)
                self.channel.queue_declare(queue=self.command_queue, durable=True)
                
                logger.info("Successfully reconnected to RabbitMQ")
                
        except Exception as e:
            logger.error(f"Failed to reconnect to RabbitMQ: {e}")


# Message Queue Factory
def create_message_queue(queue_type: str = "in_memory", **kwargs) -> MessageQueue:
    """
    Factory function to create the appropriate message queue.
    
    Args:
        queue_type: The type of queue to create ("in_memory" or "rabbitmq")
        **kwargs: Additional arguments for the queue constructor
    
    Returns:
        An instance of MessageQueue
    """
    if queue_type.lower() == "in_memory":
        return InMemoryMessageQueue()
    elif queue_type.lower() == "rabbitmq":
        required_args = ["host", "port", "username", "password"]
        for arg in required_args:
            if arg not in kwargs:
                raise ValueError(f"Missing required argument for RabbitMQ: {arg}")
        
        return RabbitMQMessageQueue(
            host=kwargs["host"],
            port=kwargs["port"],
            username=kwargs["username"],
            password=kwargs["password"],
            exchange_name=kwargs.get("exchange_name", "aihive_exchange"),
            event_queue=kwargs.get("event_queue", "event_queue"),
            command_queue=kwargs.get("command_queue", "command_queue")
        )
    else:
        raise ValueError(f"Unknown queue type: {queue_type}") 