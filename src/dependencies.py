import logging
from functools import lru_cache
from typing import Optional
from unittest.mock import AsyncMock

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import Config
from src.core.message_broker.infrastructure.rabbitmq_broker import RabbitMQBroker
from src.core.message_broker.message_broker_interface import MessageBroker
from src.task_management.application.services.task_service import TaskService
from src.task_management.domain.repositories.task_repository_interface import TaskRepositoryInterface
from src.task_management.infrastructure.repositories.mongodb_task_repository import MongoDBTaskRepository


logger = logging.getLogger(__name__)


@lru_cache()
def get_config() -> Config:
    """Get the application configuration."""
    return Config()


# MongoDB client as a singleton
_mongodb_client: Optional[AsyncIOMotorClient] = None


async def get_mongodb_client() -> AsyncIOMotorClient:
    """Get a MongoDB client."""
    global _mongodb_client
    if _mongodb_client is None:
        config = get_config()
        try:
            _mongodb_client = AsyncIOMotorClient(config.database["connection_uri"])
            # Verify that the connection works
            await _mongodb_client.admin.command("ping")
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            logger.warning("Using in-memory mock MongoDB client for documentation purposes only")
            # Create a mock client for documentation purposes
            _mongodb_client = AsyncMock()
            _mongodb_client.admin.command = AsyncMock(return_value={"ok": 1})
    return _mongodb_client


# Message broker as a singleton
_message_broker: Optional[MessageBroker] = None


async def get_message_broker() -> MessageBroker:
    """Get a message broker instance."""
    global _message_broker
    if _message_broker is None:
        try:
            _message_broker = RabbitMQBroker()
            await _message_broker.connect()
            logger.info("Connected to message broker")
        except Exception as e:
            logger.error(f"Failed to connect to message broker: {str(e)}")
            logger.warning("Using mock message broker for documentation purposes only")
            # Create a mock broker for documentation purposes
            _message_broker = AsyncMock(spec=MessageBroker)
            _message_broker.publish_event = AsyncMock()
            _message_broker.subscribe_to_event = AsyncMock()
    return _message_broker


async def get_task_repository(
    mongodb_client: AsyncIOMotorClient = Depends(get_mongodb_client)
) -> TaskRepositoryInterface:
    """Get a task repository instance."""
    repo = MongoDBTaskRepository(client=mongodb_client)
    return repo


async def get_task_service(
    task_repository: TaskRepositoryInterface = Depends(get_task_repository),
    message_broker: MessageBroker = Depends(get_message_broker)
) -> TaskService:
    """Get a task service instance."""
    return TaskService(task_repository, message_broker) 