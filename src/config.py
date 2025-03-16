import os
from typing import Dict, Any

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        self.environment = os.getenv("APP_ENV", "development")
        
        # Message queue
        self.message_queue = {
            "connection_uri": os.getenv("MESSAGE_QUEUE_URI", "amqp://guest:guest@localhost/"),
            "event_exchange": os.getenv("MESSAGE_QUEUE_EVENT_EXCHANGE", "domain_events"),
            "command_exchange": os.getenv("MESSAGE_QUEUE_COMMAND_EXCHANGE", "commands"),
            "task_assignment_queue": os.getenv("TASK_ASSIGNMENT_QUEUE", "task_assignments"),
            "notification_queue": os.getenv("NOTIFICATION_QUEUE", "notifications")
        }
        
        # Database
        self.database = {
            "connection_uri": os.getenv("DATABASE_URI", "mongodb://localhost:27017/aihive"),
            "database_name": os.getenv("DATABASE_NAME", "aihive")
        }
        
        # Task scanning
        self.task_scanning = {
            "interval_seconds": int(os.getenv("TASK_SCANNING_INTERVAL", "300")),  # 5 minutes
            "batch_size": int(os.getenv("TASK_SCANNING_BATCH_SIZE", "100"))
        }
        
        # Agent configuration
        self.agent = {
            "polling_interval_seconds": int(os.getenv("AGENT_POLLING_INTERVAL", "30")),
            "max_concurrent_tasks": int(os.getenv("AGENT_MAX_CONCURRENT_TASKS", "5"))
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        parts = key.split('.')
        obj = self
        
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return default
                
        return obj 