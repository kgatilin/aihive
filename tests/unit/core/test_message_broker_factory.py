import pytest
from unittest.mock import patch, MagicMock

from src.config import Config
from src.core.message_broker.factory import MessageBrokerFactory
from src.core.message_broker.infrastructure.rabbitmq_broker import RabbitMQBroker
from src.core.message_broker.infrastructure.in_memory_broker import InMemoryBroker


class TestMessageBrokerFactory:
    """Test suite for the MessageBrokerFactory."""
    
    def test_create_in_memory_broker_without_config(self):
        """Test that factory creates an in-memory broker when no config is provided."""
        broker = MessageBrokerFactory.create()
        assert isinstance(broker, InMemoryBroker)
    
    def test_create_in_memory_broker_explicit(self):
        """Test that factory creates an in-memory broker when explicitly requested."""
        broker = MessageBrokerFactory.create(broker_type="in_memory")
        assert isinstance(broker, InMemoryBroker)
    
    def test_create_rabbitmq_broker(self):
        """Test that factory creates a RabbitMQ broker when requested."""
        mock_config = MagicMock(spec=Config)
        mock_config.message_queue = {"connection_uri": "amqp://localhost:5672"}
        
        broker = MessageBrokerFactory.create(broker_type="rabbitmq", config=mock_config)
        assert isinstance(broker, RabbitMQBroker)
    
    def test_create_broker_from_config(self):
        """Test that factory creates the correct broker based on config."""
        # Mock config with RabbitMQ type
        mock_config = MagicMock(spec=Config)
        mock_config.message_queue = {
            "type": "rabbitmq",
            "connection_uri": "amqp://localhost:5672"
        }
        
        broker = MessageBrokerFactory.create(config=mock_config)
        assert isinstance(broker, RabbitMQBroker)
        
        # Mock config with in-memory type
        mock_config.message_queue = {"type": "in_memory"}
        broker = MessageBrokerFactory.create(config=mock_config)
        assert isinstance(broker, InMemoryBroker)
    
    def test_invalid_broker_type(self):
        """Test that factory raises ValueError for invalid broker types."""
        with pytest.raises(ValueError):
            MessageBrokerFactory.create(broker_type="invalid_type")
    
    def test_rabbitmq_requires_config(self):
        """Test that factory raises ValueError when RabbitMQ is requested without config."""
        with pytest.raises(ValueError):
            MessageBrokerFactory.create(broker_type="rabbitmq") 