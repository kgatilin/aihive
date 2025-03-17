import logging
from functools import lru_cache
from typing import AsyncGenerator

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


async def get_mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Get a MongoDB client."""
    config = get_config()
    client = AsyncIOMotorClient(config.database["connection_uri"])
    try:
        # Verify that the connection works
        await client.admin.command("ping")
        logger.info("Connected to MongoDB")
        yield client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    finally:
        client.close()
        logger.info("Closed MongoDB connection")


async def get_message_broker() -> AsyncGenerator[MessageBroker, None]:
    """Get a message broker instance."""
    broker = RabbitMQBroker()
    try:
        await broker.connect()
        logger.info("Connected to message broker")
        yield broker
    except Exception as e:
        logger.error(f"Failed to connect to message broker: {str(e)}")
        raise
    finally:
        await broker.disconnect()
        logger.info("Disconnected from message broker")


async def get_task_repository(
    mongodb_client: AsyncIOMotorClient = AsyncGenerator(get_mongodb_client)
) -> TaskRepositoryInterface:
    """Get a task repository instance."""
    return MongoDBTaskRepository(client=mongodb_client)


async def get_task_service(
    task_repository: TaskRepositoryInterface = AsyncGenerator(get_task_repository),
    message_broker: MessageBroker = AsyncGenerator(get_message_broker)
) -> TaskService:
    """Get a task service instance."""
    return TaskService(task_repository, message_broker) 