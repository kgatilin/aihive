import os
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache
import yaml
from pathlib import Path


logger = logging.getLogger(__name__)


class Config:
    """Application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If not provided, environment
                variables will be used.
        """
        self._config: Dict[str, Any] = {}

        # Default configuration
        self._config["logging"] = {
            "level": os.environ.get("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        }

        self._config["database"] = {
            "type": os.environ.get("DB_TYPE", "mongodb"),
            "connection_uri": os.environ.get(
                "MONGODB_CONNECTION_URI", "mongodb://localhost:27017/"
            ),
        }
        
        self._config["ai"] = {
            "default_model": os.environ.get("DEFAULT_AI_MODEL", "gpt-4-turbo-preview"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        }
        
        self._config["message_broker"] = {
            "type": os.environ.get("MESSAGE_BROKER_TYPE", "rabbitmq"),
            "connection_uri": os.environ.get(
                "RABBITMQ_CONNECTION_URI", "amqp://guest:guest@localhost:5672/"
            ),
        }
        
        self._config["api"] = {
            "host": os.environ.get("API_HOST", "0.0.0.0"),
            "port": int(os.environ.get("API_PORT", "8000")),
            "debug": os.environ.get("API_DEBUG", "False").lower() == "true",
        }
        
        self._config["product_definition"] = {
            "storage_type": os.environ.get("PRODUCT_REQUIREMENT_STORAGE_TYPE", "mongodb"),
            "file_storage_dir": os.environ.get("PRODUCT_REQUIREMENT_FILE_STORAGE_DIR", "data/product_requirements"),
        }

        # Load configuration from file if provided
        if config_path:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._update_recursive(self._config, yaml_config)

        # Configure logging
        self._configure_logging()

    def _update_recursive(self, original: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Update dictionary recursively.

        Args:
            original: Original dictionary to update.
            update: Dictionary with updates.
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._update_recursive(original[key], value)
            else:
                original[key] = value

    def _configure_logging(self) -> None:
        """Configure logging."""
        logging.basicConfig(
            level=self._config["logging"]["level"],
            format=self._config["logging"]["format"],
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key.

        Returns:
            Configuration value.
        """
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key.

        Returns:
            True if key exists, False otherwise.
        """
        return key in self._config

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._config
    
    @property
    def openai_api_key(self) -> str:
        """Get the OpenAI API key."""
        api_key = self._config["ai"]["openai_api_key"]
        if not api_key:
            logger.warning("OpenAI API key is not set. AI features will not work properly.")
        return api_key


@lru_cache()
def get_config(config_path: Optional[str] = None) -> Config:
    """Get the application configuration (cached).

    Args:
        config_path: Path to configuration file. If not provided, environment
            variables will be used.

    Returns:
        Application configuration.
    """
    return Config(config_path) 