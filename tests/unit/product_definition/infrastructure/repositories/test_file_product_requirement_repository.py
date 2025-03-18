"""
Tests for the FileProductRequirementRepository.
"""

import os
import json
import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.product_definition.domain.entities.product_requirement import ProductRequirement
from src.product_definition.infrastructure.repositories.file_product_requirement_repository import FileProductRequirementRepository


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storing product requirements during tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after tests
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_repository(temp_storage_dir):
    """Create a file repository instance for testing."""
    return FileProductRequirementRepository(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_product_requirement():
    """Create a sample product requirement for testing."""
    return ProductRequirement(
        product_requirement_id="test-req-001",
        title="Test Requirement",
        description="A test product requirement",
        content="# Test Requirement\n\nThis is a test requirement for unit testing.",
        created_by="test-user",
        status="draft",
        related_task_id="test-task-001",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        sections=["Introduction", "Requirements"],
        metadata={"priority": "high"}
    )


@pytest.mark.asyncio
async def test_file_repository_initialization(file_repository, temp_storage_dir):
    """Test that the repository is initialized with the correct directory."""
    assert file_repository._storage_dir == temp_storage_dir
    # Check that the directory exists
    assert os.path.exists(temp_storage_dir)
    # Check that the index file is created
    assert os.path.exists(os.path.join(temp_storage_dir, "index.json"))


@pytest.mark.asyncio
async def test_create_product_requirement(file_repository, sample_product_requirement, temp_storage_dir):
    """Test creating a product requirement in the file repository."""
    # Create a product requirement
    created_requirement = await file_repository.create(sample_product_requirement)
    
    # Check that the requirement is returned with the same ID
    assert created_requirement.product_requirement_id == sample_product_requirement.product_requirement_id
    
    # Check that a file was created
    file_path = os.path.join(temp_storage_dir, f"{sample_product_requirement.product_requirement_id}.json")
    assert os.path.exists(file_path)
    
    # Check that the content of the file is correct
    with open(file_path, "r") as f:
        content = json.load(f)
        assert content["title"] == sample_product_requirement.title
        assert content["description"] == sample_product_requirement.description
        assert content["content"] == sample_product_requirement.content
        assert content["created_by"] == sample_product_requirement.created_by
        assert content["status"] == sample_product_requirement.status
        assert content["related_task_id"] == sample_product_requirement.related_task_id
        assert content["version"] == sample_product_requirement.version
        
    # Check that the index was updated
    with open(os.path.join(temp_storage_dir, "index.json"), "r") as f:
        index = json.load(f)
        assert sample_product_requirement.product_requirement_id in index
        assert index[sample_product_requirement.product_requirement_id]["title"] == sample_product_requirement.title


@pytest.mark.asyncio
async def test_find_by_id(file_repository, sample_product_requirement):
    """Test finding a product requirement by ID."""
    # Create a product requirement
    await file_repository.create(sample_product_requirement)
    
    # Find the requirement by ID
    found_requirement = await file_repository.find_by_id(sample_product_requirement.product_requirement_id)
    
    # Check that the requirement was found and has the correct values
    assert found_requirement is not None
    assert found_requirement.product_requirement_id == sample_product_requirement.product_requirement_id
    assert found_requirement.title == sample_product_requirement.title
    assert found_requirement.description == sample_product_requirement.description
    assert found_requirement.content == sample_product_requirement.content
    assert found_requirement.created_by == sample_product_requirement.created_by
    assert found_requirement.status == sample_product_requirement.status
    assert found_requirement.related_task_id == sample_product_requirement.related_task_id
    assert found_requirement.version == sample_product_requirement.version
    assert found_requirement.sections == sample_product_requirement.sections
    assert found_requirement.metadata == sample_product_requirement.metadata


@pytest.mark.asyncio
async def test_find_by_id_not_found(file_repository):
    """Test finding a product requirement by ID when it doesn't exist."""
    # Find a non-existent requirement
    found_requirement = await file_repository.find_by_id("non-existent-id")
    
    # Check that the requirement was not found
    assert found_requirement is None


@pytest.mark.asyncio
async def test_update_product_requirement(file_repository, sample_product_requirement):
    """Test updating a product requirement."""
    # Create a product requirement
    await file_repository.create(sample_product_requirement)
    
    # Update the requirement
    sample_product_requirement.title = "Updated Title"
    sample_product_requirement.content = "Updated Content"
    sample_product_requirement.status = "review"
    sample_product_requirement.version = 2
    
    updated_requirement = await file_repository.update(sample_product_requirement)
    
    # Check that the updated requirement was returned
    assert updated_requirement.title == "Updated Title"
    assert updated_requirement.content == "Updated Content"
    assert updated_requirement.status == "review"
    assert updated_requirement.version == 2
    
    # Find the requirement to check it was actually updated
    found_requirement = await file_repository.find_by_id(sample_product_requirement.product_requirement_id)
    assert found_requirement.title == "Updated Title"
    assert found_requirement.content == "Updated Content"
    assert found_requirement.status == "review"
    assert found_requirement.version == 2
    
    # Check that the index was updated
    with open(os.path.join(file_repository._storage_dir, "index.json"), "r") as f:
        index = json.load(f)
        assert index[sample_product_requirement.product_requirement_id]["title"] == "Updated Title"
        assert index[sample_product_requirement.product_requirement_id]["status"] == "review"


@pytest.mark.asyncio
async def test_update_non_existent_requirement(file_repository, sample_product_requirement):
    """Test updating a product requirement that doesn't exist."""
    # Try to update a non-existent requirement
    # The repository should just return the requirement without error
    updated_requirement = await file_repository.update(sample_product_requirement)
    
    # Check that the requirement was returned unchanged
    assert updated_requirement == sample_product_requirement


@pytest.mark.asyncio
async def test_delete_product_requirement(file_repository, sample_product_requirement, temp_storage_dir):
    """Test deleting a product requirement."""
    # Create a product requirement
    await file_repository.create(sample_product_requirement)
    
    # Delete the requirement
    result = await file_repository.delete(sample_product_requirement.product_requirement_id)
    
    # Check that the deletion was successful
    assert result is True
    
    # Check that the file was deleted
    file_path = os.path.join(temp_storage_dir, f"{sample_product_requirement.product_requirement_id}.json")
    assert not os.path.exists(file_path)
    
    # Check that the index was updated
    with open(os.path.join(temp_storage_dir, "index.json"), "r") as f:
        index = json.load(f)
        assert sample_product_requirement.product_requirement_id not in index


@pytest.mark.asyncio
async def test_delete_non_existent_requirement(file_repository):
    """Test deleting a product requirement that doesn't exist."""
    # Try to delete a non-existent requirement
    result = await file_repository.delete("non-existent-id")
    
    # Check that the deletion was not successful
    assert result is False


@pytest.mark.asyncio
async def test_find_by_task_id(file_repository):
    """Test finding product requirements by task ID."""
    # Create several product requirements with different task IDs
    task_id = "test-task-002"
    requirements = []
    
    for i in range(3):
        req = ProductRequirement(
            product_requirement_id=f"test-req-{i+1}",
            title=f"Test Requirement {i+1}",
            description=f"Test description {i+1}",
            content=f"Test content {i+1}",
            created_by="test-user",
            status="draft",
            related_task_id=task_id if i < 2 else "other-task-id",  # First 2 with same task ID
            version=1
        )
        await file_repository.create(req)
        requirements.append(req)
    
    # Find requirements by task ID
    found_requirements = await file_repository.find_by_task_id(task_id)
    
    # Check that the correct requirements were found
    assert len(found_requirements) == 2
    assert all(req.related_task_id == task_id for req in found_requirements)
    assert {req.product_requirement_id for req in found_requirements} == {"test-req-1", "test-req-2"}


@pytest.mark.asyncio
async def test_find_by_status(file_repository):
    """Test finding product requirements by status."""
    # Create several product requirements with different statuses
    requirements = []
    for i, status in enumerate(["draft", "review", "approved", "draft"]):
        req = ProductRequirement(
            product_requirement_id=f"test-req-status-{i+1}",
            title=f"Test Status Requirement {i+1}",
            description=f"Test description {i+1}",
            content=f"Test content {i+1}",
            created_by="test-user",
            status=status,
            related_task_id=f"task-{i+1}",
            version=1
        )
        await file_repository.create(req)
        requirements.append(req)
    
    # Find requirements by status
    found_draft_requirements = await file_repository.find_by_status("draft")
    
    # Check that the correct requirements were found
    assert len(found_draft_requirements) == 2
    assert all(req.status == "draft" for req in found_draft_requirements)
    
    # Find requirements with a different status
    found_approved_requirements = await file_repository.find_by_status("approved")
    assert len(found_approved_requirements) == 1
    assert found_approved_requirements[0].status == "approved"


@pytest.mark.asyncio
async def test_find_by_created_by(file_repository):
    """Test finding product requirements by creator."""
    # Create several product requirements with different creators
    requirements = []
    for i, creator in enumerate(["user1", "user2", "user1"]):
        req = ProductRequirement(
            product_requirement_id=f"test-req-creator-{i+1}",
            title=f"Test Creator Requirement {i+1}",
            description=f"Test description {i+1}",
            content=f"Test content {i+1}",
            created_by=creator,
            status="draft",
            related_task_id=f"task-{i+1}",
            version=1
        )
        await file_repository.create(req)
        requirements.append(req)
    
    # Find requirements by creator
    found_requirements = await file_repository.find_by_created_by("user1")
    
    # Check that the correct requirements were found
    assert len(found_requirements) == 2
    assert all(req.created_by == "user1" for req in found_requirements)
    
    # Find requirements with a different creator
    found_requirements_user2 = await file_repository.find_by_created_by("user2")
    assert len(found_requirements_user2) == 1
    assert found_requirements_user2[0].created_by == "user2"


@pytest.mark.asyncio
async def test_search(file_repository):
    """Test searching for product requirements with criteria."""
    # Create several product requirements with different attributes
    requirements = []
    for i in range(5):
        status = "draft" if i % 2 == 0 else "review"
        creator = "user1" if i < 3 else "user2"
        
        req = ProductRequirement(
            product_requirement_id=f"test-req-search-{i+1}",
            title=f"Test Search Requirement {i+1}",
            description=f"Test description {i+1}",
            content=f"Test content {i+1}",
            created_by=creator,
            status=status,
            related_task_id=f"task-{(i % 2) + 1}",  # Alternate between task-1 and task-2
            version=1
        )
        await file_repository.create(req)
        requirements.append(req)
    
    # Search with combined criteria
    search_criteria = {
        "status": "draft",
        "created_by": "user1"
    }
    
    found_requirements = await file_repository.search(search_criteria)
    
    # Check that the correct requirements were found
    assert len(found_requirements) == 2  # Should find 2 requirements with draft status created by user1
    assert all(req.status == "draft" and req.created_by == "user1" for req in found_requirements)
    
    # Test a search that should return no results
    search_criteria = {
        "status": "approved",  # No requirements have this status
        "created_by": "user1"
    }
    
    found_requirements = await file_repository.search(search_criteria)
    assert len(found_requirements) == 0 