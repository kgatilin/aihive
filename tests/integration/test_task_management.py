import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.task_management.infrastructure.repositories.mongodb_task_repository import MongoDBTaskRepository
from src.task_management.application.services.task_service import TaskService
from src.core.message_broker.message_broker_interface import MessageBroker


class MockMongoDBClient:
    """Mock MongoDB client for testing."""
    
    def __init__(self):
        self.tasks = {}
        self.indexes = {}
        self.databases = {}
    
    async def admin_command(self, command):
        """Mock admin command."""
        return {"ok": 1}
    
    def close(self):
        """Mock close method."""
        pass
    
    def __getitem__(self, name):
        """Support dictionary-style access to databases."""
        if name not in self.databases:
            self.databases[name] = MockMongoDBDatabase(self)
        return self.databases[name]


class MockMongoDBDatabase:
    """Mock MongoDB database for testing."""
    
    def __init__(self, client):
        self.client = client
        self.collections = {}
    
    async def create_index(self, collection_name, keys, **kwargs):
        """Mock create_index method."""
        self.client.indexes[collection_name] = keys
    
    async def list_indexes(self, collection_name):
        """Mock list_indexes method."""
        return self.client.indexes.get(collection_name, [])
    
    def __getitem__(self, name):
        """Support dictionary-style access to collections."""
        if name not in self.collections:
            self.collections[name] = MockMongoDBCollection(self)
        return self.collections[name]
    
    def __getattr__(self, name):
        """Support attribute access to collections."""
        if name not in self.collections:
            self.collections[name] = MockMongoDBCollection(self)
        return self.collections[name]


class AsyncIterator:
    """Helper class to make an async iterator."""
    
    def __init__(self, items):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


class MockMongoDBCollection:
    """Mock MongoDB collection for testing."""
    
    def __init__(self, database):
        self.database = database
        self.documents = {}
        self.name = "tasks"  # Add name attribute for index creation
    
    async def create_index(self, keys, **kwargs):
        """Mock create_index method."""
        await self.database.create_index(self.name, keys, **kwargs)
    
    async def list_indexes(self):
        """Mock list_indexes method."""
        return await self.database.list_indexes(self.name)
    
    async def insert_one(self, document):
        """Mock insert_one method."""
        doc_id = document.get("_id", str(len(self.documents)))
        self.documents[doc_id] = document
        return MagicMock(inserted_id=doc_id)
    
    async def find_one(self, query):
        """Mock find_one method."""
        if "_id" in query:
            return self.documents.get(query["_id"])
        for doc in self.documents.values():
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    def find(self, query=None):
        """Mock find method."""
        if query is None:
            return AsyncIterator(list(self.documents.values()))
        matching_docs = [doc for doc in self.documents.values() 
                        if all(doc.get(k) == v for k, v in query.items())]
        return AsyncIterator(matching_docs)
    
    async def update_one(self, query, update, upsert=False):
        """Mock update_one method."""
        doc = await self.find_one(query)
        if doc:
            if "$set" in update:
                set_dict = update["$set"]
                for key in set_dict:
                    doc[key] = set_dict[key]
            return MagicMock(modified_count=1)
        elif upsert:
            # If upsert is True and document doesn't exist, create it
            new_doc = update.get("$set", {})
            if "_id" in query:
                new_doc["_id"] = query["_id"]
            await self.insert_one(new_doc)
            return MagicMock(modified_count=0, upserted_id=new_doc.get("_id"))
        return MagicMock(modified_count=0)
    
    async def delete_many(self, query):
        """Mock delete_many method."""
        if query == {}:
            self.documents.clear()
            return MagicMock(deleted_count=len(self.documents))
        deleted_count = 0
        for doc_id, doc in list(self.documents.items()):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.documents[doc_id]
                deleted_count += 1
        return MagicMock(deleted_count=deleted_count)


@pytest_asyncio.fixture
async def mongodb_client():
    """Create a mock MongoDB client for testing."""
    client = MockMongoDBClient()
    client.aihive_test = MockMongoDBDatabase(client)
    yield client
    client.close()


@pytest_asyncio.fixture
async def task_repository(mongodb_client):
    """Create a task repository with the mock MongoDB client."""
    repo = MongoDBTaskRepository(client=mongodb_client)
    # Override the database name to use the test database
    repo.db = mongodb_client.aihive_test
    repo.collection = repo.db.tasks
    # Create indexes
    await repo._create_indexes()
    return repo


@pytest.fixture
def mock_message_broker():
    """Create a mock message broker."""
    broker = AsyncMock(spec=MessageBroker)
    broker.publish_event = AsyncMock()
    broker.subscribe_to_event = AsyncMock()
    return broker


@pytest_asyncio.fixture
async def task_service(task_repository, mock_message_broker):
    """Create a task service with the test repository and mock broker."""
    return TaskService(task_repository, mock_message_broker)


@pytest.mark.asyncio
async def test_create_and_retrieve_task(task_service):
    """Test creating a task and retrieving it."""
    title = "Integration Test Task"
    description = "This is an integration test task"
    
    created_task = await task_service.create_task(
        title=title,
        description=description,
        priority="high",
        created_by="integration_test"
    )
    
    retrieved_task = await task_service.get_task(created_task.task_id)
    
    assert retrieved_task is not None
    assert retrieved_task.task_id == created_task.task_id
    assert retrieved_task.title == title
    assert retrieved_task.description == description
    assert retrieved_task.priority == TaskPriority.HIGH
    assert retrieved_task.created_by == "integration_test"
    assert retrieved_task.status == TaskStatus.CREATED


@pytest.mark.asyncio
async def test_task_lifecycle(task_service):
    """Test the complete lifecycle of a task."""
    # Create a task
    task = await task_service.create_task(
        title="Lifecycle Test Task",
        description="Testing the complete task lifecycle",
        priority="medium",
        created_by="integration_test"
    )
    
    # Assign the task
    task = await task_service.assign_task(
        task_id=task.task_id,
        assignee="test_assignee",
        assigned_by="integration_test"
    )
    assert task.assignee == "test_assignee"
    assert task.status == TaskStatus.ASSIGNED
    
    # Update status to IN_PROGRESS
    task = await task_service.update_task_status(
        task_id=task.task_id,
        new_status="in_progress",
        changed_by="test_assignee",
        reason="Starting work"
    )
    assert task.status == TaskStatus.IN_PROGRESS
    
    # Update status to REVIEW
    task = await task_service.update_task_status(
        task_id=task.task_id,
        new_status="review",
        changed_by="test_assignee",
        reason="Ready for review"
    )
    assert task.status == TaskStatus.REVIEW
    
    # Complete the task
    task = await task_service.complete_task(
        task_id=task.task_id,
        completed_by="test_reviewer",
        artifact_ids=["artifact-1", "artifact-2"],
        completion_notes="Completed successfully"
    )
    assert task.status == TaskStatus.COMPLETED
    
    # Retrieve the final task state
    final_task = await task_service.get_task(task.task_id)
    assert final_task.status == TaskStatus.COMPLETED
    assert "artifact-1" in final_task.artifact_ids
    assert "artifact-2" in final_task.artifact_ids


@pytest.mark.asyncio
async def test_find_tasks_by_status(task_service):
    """Test finding tasks by status."""
    # Create tasks with different statuses
    task1 = await task_service.create_task(
        title="Task 1",
        description="First test task",
        priority="low",
        created_by="integration_test"
    )
    
    task2 = await task_service.create_task(
        title="Task 2",
        description="Second test task",
        priority="medium",
        created_by="integration_test"
    )
    
    # Assign and start task2
    await task_service.assign_task(
        task_id=task2.task_id,
        assignee="test_assignee",
        assigned_by="integration_test"
    )
    
    await task_service.update_task_status(
        task_id=task2.task_id,
        new_status="in_progress",
        changed_by="test_assignee"
    )
    
    # Find tasks by status
    created_tasks = await task_service.find_tasks_by_status("created")
    in_progress_tasks = await task_service.find_tasks_by_status("in_progress")
    
    # Assert
    assert len(created_tasks) == 1
    assert created_tasks[0].task_id == task1.task_id
    
    assert len(in_progress_tasks) == 1
    assert in_progress_tasks[0].task_id == task2.task_id


@pytest.mark.asyncio
async def test_find_tasks_by_assignee(task_service):
    """Test finding tasks by assignee."""
    # Create tasks and assign to different users
    task1 = await task_service.create_task(
        title="Task for User A",
        description="Task assigned to User A",
        priority="medium",
        created_by="integration_test"
    )
    
    task2 = await task_service.create_task(
        title="Task for User B",
        description="Task assigned to User B",
        priority="high",
        created_by="integration_test"
    )
    
    # Assign tasks
    await task_service.assign_task(
        task_id=task1.task_id,
        assignee="user_a",
        assigned_by="integration_test"
    )
    
    await task_service.assign_task(
        task_id=task2.task_id,
        assignee="user_b",
        assigned_by="integration_test"
    )
    
    # Find tasks by assignee
    user_a_tasks = await task_service.find_tasks_by_assignee("user_a")
    user_b_tasks = await task_service.find_tasks_by_assignee("user_b")
    
    # Assert
    assert len(user_a_tasks) == 1
    assert user_a_tasks[0].task_id == task1.task_id
    
    assert len(user_b_tasks) == 1
    assert user_b_tasks[0].task_id == task2.task_id 