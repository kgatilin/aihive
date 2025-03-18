import asyncio
import logging
import os
from dotenv import load_dotenv
from aiohttp import web

from src.core.common.message_broker import RabbitMQBroker
from src.task_management.infrastructure.repositories.mongodb_task_repository import MongoDBTaskRepository
from src.task_management.application.task_service import TaskService
from src.orchestration.domain.orchestrator_agent import ProductRefinementOrchestrator
from src.human_interaction.api.task_api import TaskApi, setup_routes


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def start_web_app(task_service):
    """Start the web application."""
    app = web.Application()
    
    # Create API handlers
    task_api = TaskApi(task_service)
    
    # Setup routes
    setup_routes(app, task_api)
    
    # Configure CORS if needed
    # cors = aiohttp_cors.setup(app, defaults={
    #     "*": aiohttp_cors.ResourceOptions(
    #         allow_credentials=True,
    #         expose_headers="*",
    #         allow_headers="*"
    #     )
    # })
    
    # Get port from environment or use default
    port = int(os.getenv("API_PORT", "8080"))
    
    # Start the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Web API running at http://0.0.0.0:{port}")
    
    return runner


async def main():
    # Load environment variables
    load_dotenv()
    logger.info("Starting AI-Driven Development Pipeline")
    
    try:
        # Initialize infrastructure components
        message_broker = RabbitMQBroker()
        await message_broker.connect()
        logger.info("Connected to message broker")
        
        task_repository = MongoDBTaskRepository()
        await task_repository.connect()
        logger.info("Connected to task repository")
        
        # Initialize application services
        task_service = TaskService(task_repository, message_broker)
        
        # Initialize orchestration agents
        product_orchestrator = ProductRefinementOrchestrator(message_broker, task_service)
        await product_orchestrator.start()
        logger.info("Started Product Refinement Orchestrator")
        
        # Start the web API
        runner = await start_web_app(task_service)
        
        # Keep the application running
        logger.info("Application running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}")
    finally:
        # Cleanup
        try:
            await product_orchestrator.stop()
            await message_broker.disconnect()
            await task_repository.disconnect()
            await runner.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 