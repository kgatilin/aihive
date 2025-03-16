import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from src.config import Config
from src.task_management.domain.task import Task, TaskStatus, TaskPriority
from src.task_management.domain.task_repository import TaskRepository


logger = logging.getLogger(__name__)


class MongoTaskRepository(TaskRepository):
    """MongoDB implementation of the TaskRepository interface."""
    
    def __init__(self):
        self.config = Config()
        self.client = None
        self.collection = None
    
    async def connect(self) -> None:
        """Connect to MongoDB and setup the collection."""
        if self.client is not None:
            return  # Already connected
        
        try:
            # Connect to MongoDB
            connection_uri = self.config.database["connection_uri"]
            database_name = self.config.database["database_name"]
            
            self.client = AsyncIOMotorClient(connection_uri)
            database = self.client[database_name]
            self.collection = database["tasks"]
            
            # Create indexes
            await self.collection.create_index("task_id", unique=True)
            await self.collection.create_index("status")
            await self.collection.create_index("assignee")
            
            logger.info(f"Connected to MongoDB at {connection_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.collection = None
            logger.info("Disconnected from MongoDB")
    
    def _to_document(self, task: Task) -> Dict[str, Any]:
        """Convert a Task domain entity to a MongoDB document."""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "created_by": task.created_by,
            "assignee": task.assignee,
            "due_date": task.due_date,
            "requirements_ids": task.requirements_ids,
            "parent_task_id": task.parent_task_id,
            "tags": task.tags,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
    
    def _to_entity(self, document: Dict[str, Any]) -> Task:
        """Convert a MongoDB document to a Task domain entity."""
        return Task(
            task_id=document.get("task_id"),
            title=document.get("title", ""),
            description=document.get("description", ""),
            priority=document.get("priority", TaskPriority.MEDIUM.value),
            status=document.get("status", TaskStatus.CREATED.value),
            created_by=document.get("created_by", ""),
            assignee=document.get("assignee"),
            due_date=document.get("due_date"),
            requirements_ids=document.get("requirements_ids", []),
            parent_task_id=document.get("parent_task_id"),
            tags=document.get("tags", []),
            created_at=document.get("created_at", datetime.utcnow()),
            updated_at=document.get("updated_at", datetime.utcnow())
        )
    
    async def save(self, task: Task) -> None:
        """Save a Task to the repository."""
        if not self.collection:
            await self.connect()
        
        document = self._to_document(task)
        
        # Update the document if it exists, otherwise insert it
        await self.collection.replace_one(
            {"task_id": task.task_id},
            document,
            upsert=True
        )
        logger.debug(f"Saved task {task.task_id}")
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get a Task by its ID."""
        if not self.collection:
            await self.connect()
        
        document = await self.collection.find_one({"task_id": task_id})
        if document:
            return self._to_entity(document)
        return None
    
    async def find_by_status(self, status: str) -> List[Task]:
        """Find Tasks by their status."""
        if not self.collection:
            await self.connect()
        
        cursor = self.collection.find({"status": status})
        tasks = []
        
        async for document in cursor:
            tasks.append(self._to_entity(document))
        
        return tasks
    
    async def find_by_assignee(self, assignee: str) -> List[Task]:
        """Find Tasks assigned to a specific assignee."""
        if not self.collection:
            await self.connect()
        
        cursor = self.collection.find({"assignee": assignee})
        tasks = []
        
        async for document in cursor:
            tasks.append(self._to_entity(document))
        
        return tasks
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find Tasks matching the given criteria."""
        if not self.collection:
            await self.connect()
        
        cursor = self.collection.find(criteria)
        tasks = []
        
        async for document in cursor:
            tasks.append(self._to_entity(document))
        
        return tasks
    
    async def delete(self, task_id: str) -> bool:
        """Delete a Task by its ID. Returns True if successful."""
        if not self.collection:
            await self.connect()
        
        result = await self.collection.delete_one({"task_id": task_id})
        deleted = result.deleted_count > 0
        
        if deleted:
            logger.debug(f"Deleted task {task_id}")
        
        return deleted 