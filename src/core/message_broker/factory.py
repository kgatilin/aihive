from typing import Optional

from src.config import Config
from src.core.message_broker.message_broker_interface import MessageBroker
from src.core.message_broker.infrastructure.rabbitmq_broker import RabbitMQBroker
from src.core.message_broker.infrastructure.in_memory_broker import InMemoryBroker


class MessageBrokerFactory:
    """Factory class for creating message brokers."""
    
    @staticmethod
    def create(broker_type: str = None, config: Optional[Config] = None) -> MessageBroker:
        """
        Create a message broker instance based on the specified type.
        
        Args:
            broker_type: Type of broker to create ('rabbitmq' or 'in_memory')
            config: Configuration object (required for RabbitMQ)
        
        Returns:
            An instance of MessageBroker
        
        Raises:
            ValueError: If broker_type is invalid or if config is missing for RabbitMQ
        """
        if broker_type is None:
            broker_type = config.message_queue.get("type", "in_memory") if config else "in_memory"
        
        broker_type = broker_type.lower()
        
        if broker_type == "rabbitmq":
            if not config:
                raise ValueError("Config is required for RabbitMQ broker")
            return RabbitMQBroker()
        elif broker_type == "in_memory":
            return InMemoryBroker()
        else:
            raise ValueError(f"Unknown broker type: {broker_type}") 