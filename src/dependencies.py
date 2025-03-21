"""
Dependencies module for dependency injection.
"""

import logging
import os
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

from src.core.agent.orchestrator_agent import OrchestratorAgent
from src.core.agent.tool_registry import ToolRegistry
from src.product_definition.agents.product_manager_agent import ProductManagerAgent
from src.product_definition.agents.prd_template_tool import PRDTemplateTool
from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.infrastructure.repositories.mongodb_product_requirement_repository import MongoDBProductRequirementRepository
from src.product_definition.infrastructure.repositories.file_product_requirement_repository import FileProductRequirementRepository

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
            _mongodb_client = AsyncIOMotorClient(config["database"]["connection_uri"])
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


async def get_product_requirement_repository(
    mongodb_client: AsyncIOMotorClient = Depends(get_mongodb_client)
) -> ProductRequirementRepositoryInterface:
    """Get a product requirement repository instance based on configuration."""
    config = get_config()
    storage_type = config["product_definition"]["storage_type"].lower()
    
    if storage_type == "mongodb":
        logger.info("Using MongoDB for product requirement storage")
        repo = MongoDBProductRequirementRepository(client=mongodb_client)
    elif storage_type == "file":
        logger.info("Using file-based storage for product requirements")
        storage_dir = config["product_definition"]["file_storage_dir"]
        # Ensure the directory exists
        os.makedirs(storage_dir, exist_ok=True)
        repo = FileProductRequirementRepository(storage_dir=storage_dir)
    else:
        logger.warning(f"Unknown storage type '{storage_type}', falling back to MongoDB")
        repo = MongoDBProductRequirementRepository(client=mongodb_client)
    
    return repo


# Tool registry as a singleton
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        # Register common tools
        _tool_registry.register_tool(PRDTemplateTool())
    return _tool_registry


# AI agents are lazy-loaded singletons
_product_manager_agent: Optional[ProductManagerAgent] = None
_orchestrator_agent: Optional[OrchestratorAgent] = None


async def get_product_manager_agent(
    task_service: TaskService = Depends(get_task_service),
    product_requirement_repository: ProductRequirementRepositoryInterface = Depends(get_product_requirement_repository),
    tool_registry: ToolRegistry = Depends(get_tool_registry)
) -> ProductManagerAgent:
    """Get the Product Manager Agent instance."""
    global _product_manager_agent
    if _product_manager_agent is None:
        config = get_config()
        _product_manager_agent = ProductManagerAgent(
            task_service=task_service,
            product_requirement_repository=product_requirement_repository,
            tool_registry=tool_registry,
            agent_id="product-manager-agent",
            model_name=config["ai"]["default_model"]
        )
    return _product_manager_agent


async def get_orchestrator_agent(
    task_service: TaskService = Depends(get_task_service),
    product_manager_agent: ProductManagerAgent = Depends(get_product_manager_agent)
) -> OrchestratorAgent:
    """Get the Orchestrator Agent instance."""
    global _orchestrator_agent
    if _orchestrator_agent is None:
        config = get_config()
        _orchestrator_agent = OrchestratorAgent(
            task_service=task_service,
            agents={"product-manager-agent": product_manager_agent},
            agent_id="orchestrator-agent",
            model_name=config["ai"]["default_model"]
        )
    return _orchestrator_agent 