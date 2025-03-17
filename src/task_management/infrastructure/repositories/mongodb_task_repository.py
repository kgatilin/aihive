import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.repositories.task_repository_interface import TaskRepositoryInterface
from src.config import Config


logger = logging.getLogger(__name__)


class MongoDBTaskRepository(TaskRepositoryInterface):
    """MongoDB implementation of the task repository interface."""
    
    def __init__(self, client: Optional[AsyncIOMotorClient] = None):
        """Initialize the repository with a MongoDB client."""
        self.config = Config()
        self.client = client or AsyncIOMotorClient(self.config.database["connection_uri"])
        self.db: AsyncIOMotorDatabase = self.client[self.config.database["database_name"]]
        self.collection: AsyncIOMotorCollection = self.db["tasks"]
        
        # Create indexes if needed
        self._create_indexes()
    
    async def _create_indexes(self) -> None:
        """Create database indexes for common queries."""
        try:
            # Index for looking up by ID fast
            await self.collection.create_index("task_id", unique=True)
            
            # Indexes for common queries
            await self.collection.create_index("status")
            await self.collection.create_index("assignee")
            await self.collection.create_index("due_date")
            await self.collection.create_index("tags")
            await self.collection.create_index("parent_task_id")
            await self.collection.create_index("created_at")
            
            logger.info("Created task repository indexes")
        except Exception as e:
            logger.warning(f"Failed to create task repository indexes: {str(e)}")
    
    async def save(self, task: Task) -> None:
        """Save a task to the repository."""
        try:
            # Convert task to dictionary
            task_dict = task.to_dict()
            
            # Use upsert to insert or update
            await self.collection.update_one(
                {"task_id": task.task_id},
                {"$set": task_dict},
                upsert=True
            )
            logger.debug(f"Saved task {task.task_id} to MongoDB")
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id}: {str(e)}")
            raise
    
    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        try:
            task_dict = await self.collection.find_one({"task_id": task_id})
            if task_dict:
                # Convert _id to string and remove it to avoid serialization issues
                if "_id" in task_dict:
                    del task_dict["_id"]
                return Task.from_dict(task_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            raise
    
    async def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Find tasks by status."""
        try:
            cursor = self.collection.find({"status": status.value})
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by status {status.value}: {str(e)}")
            raise
    
    async def find_by_assignee(self, assignee: str) -> List[Task]:
        """Find tasks by assignee."""
        try:
            cursor = self.collection.find({"assignee": assignee})
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by assignee {assignee}: {str(e)}")
            raise
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Task]:
        """Find tasks by arbitrary criteria."""
        try:
            # Convert status and priority to their string values for MongoDB
            query = {}
            for key, value in criteria.items():
                if key == "status" and hasattr(value, "value"):
                    query[key] = value.value
                elif key == "priority" and hasattr(value, "value"):
                    query[key] = value.value
                else:
                    query[key] = value
            
            cursor = self.collection.find(query)
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by criteria {criteria}: {str(e)}")
            raise
    
    async def delete(self, task_id: str) -> bool:
        """Delete a task from the repository."""
        try:
            result = await self.collection.delete_one({"task_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            raise
    
    async def find_by_due_date_range(self, start_date: datetime, end_date: datetime) -> List[Task]:
        """Find tasks with due dates in the specified range."""
        try:
            cursor = self.collection.find({
                "due_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            })
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by due date range: {str(e)}")
            raise
    
    async def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Task]:
        """Find tasks by tags."""
        try:
            query = {"tags": {"$all": tags}} if match_all else {"tags": {"$in": tags}}
            cursor = self.collection.find(query)
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by tags {tags}: {str(e)}")
            raise
    
    async def find_by_parent_task(self, parent_task_id: str) -> List[Task]:
        """Find tasks that are children of the specified parent task."""
        try:
            cursor = self.collection.find({"parent_task_id": parent_task_id})
            tasks = []
            async for task_dict in cursor:
                if "_id" in task_dict:
                    del task_dict["_id"]
                tasks.append(Task.from_dict(task_dict))
            return tasks
        except Exception as e:
            logger.error(f"Failed to find tasks by parent task {parent_task_id}: {str(e)}")
            raise 