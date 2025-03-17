import logging
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import Config
from src.task_management.api.task_controller import router as task_router
from src.orchestration.domain.orchestrator_agent import ProductRefinementOrchestrator
from src.dependencies import get_task_service, get_message_broker


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global reference to the orchestrator
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Startup
    logger.info("Starting application...")
    
    # Start the orchestrator
    global orchestrator
    
    # Get dependencies
    task_service = await anext(get_task_service())
    message_broker = await anext(get_message_broker())
    
    # Create and start the orchestrator
    orchestrator = ProductRefinementOrchestrator(task_service, message_broker)
    await orchestrator.start()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop the orchestrator
    if orchestrator:
        await orchestrator.stop()
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = Config()
    
    app = FastAPI(
        title="AI Hive Task Management API",
        description="API for managing tasks in the AI Hive system",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api["cors_origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(task_router)
    
    return app


app = create_app()


@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {
        "message": "Welcome to the AI Hive Task Management API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    ) 