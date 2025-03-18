import os
import logging
from typing import Dict, List, Any
from functools import lru_cache


logger = logging.getLogger(__name__)


class Config:
    """Configuration for the application."""
    
    def __init__(self):
        """Initialize the configuration."""
        # Database configuration
        self.database = {
            "connection_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            "database_name": os.getenv("MONGODB_DB", "aihive"),
        }
        
        # Message queue configuration
        self.message_queue = {
            "connection_uri": os.getenv("RABBITMQ_URI", "amqp://guest:guest@localhost:5672/"),
            "event_exchange": os.getenv("RABBITMQ_EVENT_EXCHANGE", "aihive.events"),
            "command_exchange": os.getenv("RABBITMQ_COMMAND_EXCHANGE", "aihive.commands"),
        }
        
        # API configuration
        self.api = {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "cors_origins": self._parse_cors_origins(),
        }
        
        # Logging configuration
        self.logging = {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }
        
        # Agent configuration
        self.agent = {
            "polling_interval_seconds": int(os.getenv("AGENT_POLLING_INTERVAL", "60")),
            "max_concurrent_tasks": int(os.getenv("AGENT_MAX_CONCURRENT_TASKS", "10")),
        }
        
        # AI configuration
        self.ai = {
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4-turbo-preview"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        }
    
    def _parse_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        origins_str = os.getenv("CORS_ORIGINS", "*")
        if origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in origins_str.split(",")]
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            "database": self.database,
            "message_queue": self.message_queue,
            "api": self.api,
            "logging": self.logging,
            "agent": self.agent,
            "ai": self.ai,
        }
    
    @property
    def openai_api_key(self) -> str:
        """Get the OpenAI API key."""
        api_key = self.ai["openai_api_key"]
        if not api_key:
            logger.warning("OpenAI API key is not set. AI features will not work properly.")
        return api_key


@lru_cache()
def get_config() -> Config:
    """Get the application configuration (cached)."""
    return Config() 