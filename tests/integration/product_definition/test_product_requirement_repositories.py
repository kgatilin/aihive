"""
Integration tests for product requirement repositories.

These tests verify that both MongoDB and file-based repositories
correctly implement the ProductRequirementRepositoryInterface.
"""

import os
import uuid
import pytest
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient

from src.product_definition.domain.entities.product_requirement import ProductRequirement
from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.infrastructure.repositories.mongodb_product_requirement_repository import MongoDBProductRequirementRepository
from src.product_definition.infrastructure.repositories.file_product_requirement_repository import FileProductRequirementRepository


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for file-based storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after tests
    shutil.rmtree(temp_dir)


@pytest.fixture
async def mongodb_client():
    """Create a MongoDB client for testing."""
    # Use a test database
    connection_uri = os.environ.get("MONGODB_CONNECTION_URI", "mongodb://localhost:27017/")
    client = AsyncIOMotorClient(connection_uri)
    yield client
    
    # Clean up the test database
    await client.aihive_test.product_requirements.delete_many({})


@pytest.fixture
async def mongodb_repository(mongodb_client):
    """Create a MongoDB repository instance for testing."""
    repo = MongoDBProductRequirementRepository(
        client=mongodb_client,
        database_name="aihive_test",
        collection_name="product_requirements"
    )
    return repo


@pytest.fixture
async def file_repository(temp_storage_dir):
    """Create a file repository instance for testing."""
    repo = FileProductRequirementRepository(storage_dir=temp_storage_dir)
    return repo


@pytest.fixture
def sample_requirement_data():
    """Sample product requirement data for testing."""
    return {
        "product_requirement_id": f"test-req-{uuid.uuid4()}",
        "title": "Test Integration Requirement",
        "description": "A test product requirement for integration testing",
        "content": "# Test Requirement\n\nThis is a test requirement for integration testing.",
        "created_by": "integration-test",
        "status": "draft",
        "related_task_id": "test-task-001",
        "version": 1,
        "sections": ["Introduction", "Requirements"],
        "metadata": {"priority": "high", "test": True}
    }


async def run_repository_test(repo: ProductRequirementRepositoryInterface, req_data: Dict[str, Any]):
    """
    Run standard tests against a repository implementation.
    
    Args:
        repo: The repository to test
        req_data: The requirement data to use
    """
    # Create a product requirement
    requirement = ProductRequirement(**req_data)
    created = await repo.create(requirement)
    
    # Verify creation
    assert created.product_requirement_id == req_data["product_requirement_id"]
    assert created.title == req_data["title"]
    
    # Find by ID
    found = await repo.find_by_id(req_data["product_requirement_id"])
    assert found is not None
    assert found.title == req_data["title"]
    assert found.description == req_data["description"]
    assert found.metadata == req_data["metadata"]
    
    # Update the requirement
    found.title = "Updated Title"
    found.status = "review"
    found.version = 2
    updated = await repo.update(found)
    assert updated.title == "Updated Title"
    assert updated.status == "review"
    assert updated.version == 2
    
    # Verify the update was persisted
    found_again = await repo.find_by_id(req_data["product_requirement_id"])
    assert found_again.title == "Updated Title"
    assert found_again.status == "review"
    
    # Test find by task ID
    by_task = await repo.find_by_task_id(req_data["related_task_id"])
    assert len(by_task) == 1
    assert by_task[0].product_requirement_id == req_data["product_requirement_id"]
    
    # Test find by status
    by_status = await repo.find_by_status("review")
    assert len(by_status) >= 1
    assert any(r.product_requirement_id == req_data["product_requirement_id"] for r in by_status)
    
    # Test find by created by
    by_created = await repo.find_by_created_by(req_data["created_by"])
    assert len(by_created) >= 1
    assert any(r.product_requirement_id == req_data["product_requirement_id"] for r in by_created)
    
    # Test search
    search_results = await repo.search({
        "status": "review",
        "created_by": req_data["created_by"]
    })
    assert len(search_results) >= 1
    assert any(r.product_requirement_id == req_data["product_requirement_id"] for r in search_results)
    
    # Test delete
    deleted = await repo.delete(req_data["product_requirement_id"])
    assert deleted is True
    
    # Verify deletion
    not_found = await repo.find_by_id(req_data["product_requirement_id"])
    assert not_found is None


@pytest.mark.asyncio
async def test_mongodb_repository(mongodb_repository, sample_requirement_data):
    """Test the MongoDB repository implementation."""
    await run_repository_test(mongodb_repository, sample_requirement_data)


@pytest.mark.asyncio
async def test_file_repository(file_repository, sample_requirement_data):
    """Test the file repository implementation."""
    # Modify the ID to avoid conflicts
    sample_requirement_data["product_requirement_id"] = f"file-req-{uuid.uuid4()}"
    await run_repository_test(file_repository, sample_requirement_data)


@pytest.mark.asyncio
async def test_both_repositories_with_same_interface(
    mongodb_repository, file_repository, sample_requirement_data
):
    """Test that both repositories implement the same interface correctly."""
    # Test MongoDB repository
    mongo_data = sample_requirement_data.copy()
    mongo_data["product_requirement_id"] = f"mongo-{uuid.uuid4()}"
    mongo_data["title"] = "MongoDB Test"
    mongo_requirement = ProductRequirement(**mongo_data)
    mongo_created = await mongodb_repository.create(mongo_requirement)
    
    # Test File repository
    file_data = sample_requirement_data.copy()
    file_data["product_requirement_id"] = f"file-{uuid.uuid4()}"
    file_data["title"] = "File Test"
    file_requirement = ProductRequirement(**file_data)
    file_created = await file_repository.create(file_requirement)
    
    # Verify both were created correctly
    mongo_found = await mongodb_repository.find_by_id(mongo_created.product_requirement_id)
    file_found = await file_repository.find_by_id(file_created.product_requirement_id)
    
    assert mongo_found is not None
    assert file_found is not None
    assert mongo_found.title == "MongoDB Test"
    assert file_found.title == "File Test"
    
    # Clean up
    await mongodb_repository.delete(mongo_created.product_requirement_id)
    await file_repository.delete(file_created.product_requirement_id) 