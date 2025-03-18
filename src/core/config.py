"""
Configuration management for the application.
"""

import os
from typing import Optional, Dict, Any
from src.core.prompt_manager import get_prompt_manager, PromptManager


class Config:
    """
    Configuration manager for the application.
    Loads settings from environment variables with sensible defaults.
    """
    
    def __init__(self, env_vars: Optional[Dict[str, str]] = None, prompt_file_path: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            env_vars: Optional dictionary to override environment variables
            prompt_file_path: Optional path to the prompt config file
        """
        self._env_vars = env_vars or os.environ
        
        # Initialize prompt manager
        self._prompt_manager = None if prompt_file_path is None else PromptManager(prompt_file_path)
        
        # Application settings
        self._app_env = self._get_env("APP_ENV", "development")
        self._api_port = int(self._get_env("API_PORT", "8080"))
        
        # Database settings
        self._database_uri = self._get_env("DATABASE_URI", "sqlite:///aihive.db")
        self._database_name = self._get_env("DATABASE_NAME", "aihive")
        
        # Message queue settings
        self._message_queue_uri = self._get_env("MESSAGE_QUEUE_URI", "amqp://guest:guest@localhost:5672/")
        self._message_queue_event_exchange = self._get_env("MESSAGE_QUEUE_EVENT_EXCHANGE", "aihive.events")
        self._task_assignment_queue = self._get_env("TASK_ASSIGNMENT_QUEUE", "aihive.tasks.assignment")
        
        # Task scanning settings
        self._task_scanning_interval = int(self._get_env("TASK_SCANNING_INTERVAL", "60"))  # seconds
        self._task_scanning_batch_size = int(self._get_env("TASK_SCANNING_BATCH_SIZE", "100"))
        
        # Agent settings
        self._agent_polling_interval = int(self._get_env("AGENT_POLLING_INTERVAL", "5"))  # seconds
        self._agent_max_concurrent_tasks = int(self._get_env("AGENT_MAX_CONCURRENT_TASKS", "3"))
        
        # OpenAI settings
        self._openai_api_key = self._get_env("OPENAI_API_KEY", None)
        self._openai_default_model = self._get_env("OPENAI_DEFAULT_MODEL", "gpt-4-turbo-preview")
        self._openai_temperature = float(self._get_env("OPENAI_TEMPERATURE", "0.7"))
    
    def _get_env(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable value.
        
        Args:
            key: The environment variable key
            default: The default value if not found
            
        Returns:
            The value of the environment variable or the default
        """
        return self._env_vars.get(key, default)
    
    @property
    def app_env(self) -> str:
        """Get the application environment."""
        return self._app_env
    
    @property
    def api_port(self) -> int:
        """Get the API port number."""
        return self._api_port
    
    @property
    def database_uri(self) -> str:
        """Get the database URI."""
        return self._database_uri
    
    @property
    def database_name(self) -> str:
        """Get the database name."""
        return self._database_name
    
    @property
    def message_queue_uri(self) -> str:
        """Get the message queue URI."""
        return self._message_queue_uri
    
    @property
    def message_queue_event_exchange(self) -> str:
        """Get the message queue event exchange name."""
        return self._message_queue_event_exchange
    
    @property
    def task_assignment_queue(self) -> str:
        """Get the task assignment queue name."""
        return self._task_assignment_queue
    
    @property
    def task_scanning_interval(self) -> int:
        """Get the task scanning interval in seconds."""
        return self._task_scanning_interval
    
    @property
    def task_scanning_batch_size(self) -> int:
        """Get the task scanning batch size."""
        return self._task_scanning_batch_size
    
    @property
    def agent_polling_interval(self) -> int:
        """Get the agent polling interval in seconds."""
        return self._agent_polling_interval
    
    @property
    def agent_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks per agent."""
        return self._agent_max_concurrent_tasks
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get the OpenAI API key."""
        return self._openai_api_key
    
    @property
    def openai_default_model(self) -> str:
        """Get the default OpenAI model."""
        return self._openai_default_model
    
    @property
    def openai_temperature(self) -> float:
        """Get the OpenAI temperature setting."""
        return self._openai_temperature
    
    @property
    def prompt_manager(self) -> PromptManager:
        """Get the prompt manager instance."""
        return self._prompt_manager or get_prompt_manager()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        The configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Global configuration instance
_config_instance = None 