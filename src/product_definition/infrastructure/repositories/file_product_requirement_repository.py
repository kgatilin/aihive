"""
File-based implementation of the Product Requirement Repository.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.domain.entities.product_requirement import ProductRequirement

logger = logging.getLogger(__name__)


class FileProductRequirementRepository(ProductRequirementRepositoryInterface):
    """
    File-based implementation of the product requirement repository.
    
    This repository stores each product requirement as a separate JSON file
    and maintains an index file for quick lookups and filtering.
    """
    
    def __init__(self, storage_dir: str):
        """
        Initialize the file repository.
        
        Args:
            storage_dir: Directory where product requirements will be stored.
        """
        self._storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize or load the index file
        self._index_path = os.path.join(storage_dir, "index.json")
        if not os.path.exists(self._index_path):
            with open(self._index_path, "w") as f:
                json.dump({}, f)
        
        logger.info(f"Initialized file product requirement repository at {storage_dir}")
    
    async def create(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Create a new product requirement.
        
        Args:
            product_requirement: The product requirement to create.
            
        Returns:
            The created product requirement with its ID.
        """
        # Ensure the product requirement has an ID
        if not product_requirement.product_requirement_id:
            raise ValueError("Product requirement ID must be provided")
        
        # Ensure created_at and updated_at are properly set
        now = datetime.utcnow()
        if not product_requirement.created_at:
            product_requirement.created_at = now
        if not product_requirement.updated_at:
            product_requirement.updated_at = now
        
        # Save the product requirement to a file
        file_path = os.path.join(self._storage_dir, f"{product_requirement.product_requirement_id}.json")
        requirement_dict = self._to_dict(product_requirement)
        
        with open(file_path, "w") as f:
            json.dump(requirement_dict, f, indent=2, default=str)
        
        # Update the index
        await self._update_index(product_requirement)
        
        logger.info(f"Created product requirement with ID {product_requirement.product_requirement_id}")
        return product_requirement
    
    async def find_by_id(self, product_requirement_id: str) -> Optional[ProductRequirement]:
        """
        Find a product requirement by its ID.
        
        Args:
            product_requirement_id: The ID of the product requirement.
            
        Returns:
            The product requirement if found, None otherwise.
        """
        file_path = os.path.join(self._storage_dir, f"{product_requirement_id}.json")
        if not os.path.exists(file_path):
            logger.debug(f"Product requirement with ID {product_requirement_id} not found")
            return None
        
        with open(file_path, "r") as f:
            requirement_dict = json.load(f)
        
        logger.debug(f"Found product requirement with ID {product_requirement_id}")
        return self._from_dict(requirement_dict)
    
    async def update(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Update an existing product requirement.
        
        Args:
            product_requirement: The product requirement to update.
            
        Returns:
            The updated product requirement.
        """
        # Check if the product requirement exists
        file_path = os.path.join(self._storage_dir, f"{product_requirement.product_requirement_id}.json")
        if not os.path.exists(file_path):
            logger.warning(f"No product requirement found with ID {product_requirement.product_requirement_id} for update")
            return product_requirement
        
        # Update the product requirement
        product_requirement.updated_at = datetime.utcnow()
        requirement_dict = self._to_dict(product_requirement)
        
        with open(file_path, "w") as f:
            json.dump(requirement_dict, f, indent=2, default=str)
        
        # Update the index
        await self._update_index(product_requirement)
        
        logger.info(f"Updated product requirement with ID {product_requirement.product_requirement_id}")
        return product_requirement
    
    async def delete(self, product_requirement_id: str) -> bool:
        """
        Delete a product requirement.
        
        Args:
            product_requirement_id: The ID of the product requirement to delete.
            
        Returns:
            True if the product requirement was deleted, False otherwise.
        """
        file_path = os.path.join(self._storage_dir, f"{product_requirement_id}.json")
        if not os.path.exists(file_path):
            logger.warning(f"No product requirement found with ID {product_requirement_id} for deletion")
            return False
        
        # Delete the file
        os.remove(file_path)
        
        # Update the index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        if product_requirement_id in index:
            del index[product_requirement_id]
            
            with open(self._index_path, "w") as f:
                json.dump(index, f, indent=2)
        
        logger.info(f"Deleted product requirement with ID {product_requirement_id}")
        return True
    
    async def find_by_task_id(self, task_id: str) -> List[ProductRequirement]:
        """
        Find product requirements related to a task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            A list of product requirements related to the task.
        """
        # Load the index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        # Filter requirements by task ID
        requirement_ids = [
            req_id for req_id, req_data in index.items()
            if req_data.get("related_task_id") == task_id
        ]
        
        # Load each requirement
        requirements = []
        for req_id in requirement_ids:
            requirement = await self.find_by_id(req_id)
            if requirement:
                requirements.append(requirement)
        
        logger.debug(f"Found {len(requirements)} product requirements for task ID {task_id}")
        return requirements
    
    async def find_by_status(self, status: str) -> List[ProductRequirement]:
        """
        Find product requirements by status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            A list of product requirements with the specified status.
        """
        # Load the index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        # Filter requirements by status
        requirement_ids = [
            req_id for req_id, req_data in index.items()
            if req_data.get("status") == status
        ]
        
        # Load each requirement
        requirements = []
        for req_id in requirement_ids:
            requirement = await self.find_by_id(req_id)
            if requirement:
                requirements.append(requirement)
        
        logger.debug(f"Found {len(requirements)} product requirements with status {status}")
        return requirements
    
    async def find_by_created_by(self, created_by: str) -> List[ProductRequirement]:
        """
        Find product requirements by creator.
        
        Args:
            created_by: The ID of the creator.
            
        Returns:
            A list of product requirements created by the specified user or agent.
        """
        # Load the index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        # Filter requirements by creator
        requirement_ids = [
            req_id for req_id, req_data in index.items()
            if req_data.get("created_by") == created_by
        ]
        
        # Load each requirement
        requirements = []
        for req_id in requirement_ids:
            requirement = await self.find_by_id(req_id)
            if requirement:
                requirements.append(requirement)
        
        logger.debug(f"Found {len(requirements)} product requirements created by {created_by}")
        return requirements
    
    async def search(self, query: Dict[str, Any]) -> List[ProductRequirement]:
        """
        Search for product requirements based on criteria.
        
        Args:
            query: A dictionary of search criteria.
            
        Returns:
            A list of product requirements matching the criteria.
        """
        # Load the index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        # Filter requirements by the query criteria
        requirement_ids = []
        for req_id, req_data in index.items():
            matched = True
            for key, value in query.items():
                if key not in req_data or req_data[key] != value:
                    matched = False
                    break
            
            if matched:
                requirement_ids.append(req_id)
        
        # Load each requirement
        requirements = []
        for req_id in requirement_ids:
            requirement = await self.find_by_id(req_id)
            if requirement:
                requirements.append(requirement)
        
        logger.debug(f"Found {len(requirements)} product requirements matching search criteria")
        return requirements
    
    async def _update_index(self, product_requirement: ProductRequirement) -> None:
        """
        Update the index file with the product requirement data.
        
        Args:
            product_requirement: The product requirement to update in the index.
        """
        # Load the current index
        with open(self._index_path, "r") as f:
            index = json.load(f)
        
        # Update the index with this requirement's key data
        index[product_requirement.product_requirement_id] = {
            "title": product_requirement.title,
            "status": product_requirement.status,
            "created_by": product_requirement.created_by,
            "related_task_id": product_requirement.related_task_id,
            "version": product_requirement.version,
            "created_at": str(product_requirement.created_at),
            "updated_at": str(product_requirement.updated_at)
        }
        
        # Save the updated index
        with open(self._index_path, "w") as f:
            json.dump(index, f, indent=2)
    
    def _to_dict(self, product_requirement: ProductRequirement) -> Dict[str, Any]:
        """
        Convert a ProductRequirement to a dictionary for file storage.
        
        Args:
            product_requirement: The product requirement to convert.
            
        Returns:
            A dictionary representation of the product requirement.
        """
        requirement_dict = {
            "product_requirement_id": product_requirement.product_requirement_id,
            "title": product_requirement.title,
            "description": product_requirement.description,
            "content": product_requirement.content,
            "created_by": product_requirement.created_by,
            "status": product_requirement.status,
            "related_task_id": product_requirement.related_task_id,
            "version": product_requirement.version,
            "sections": product_requirement.sections or [],
            "metadata": product_requirement.metadata or {},
        }
        
        if product_requirement.created_at:
            requirement_dict["created_at"] = str(product_requirement.created_at)
        if product_requirement.updated_at:
            requirement_dict["updated_at"] = str(product_requirement.updated_at)
        if product_requirement.updated_by:
            requirement_dict["updated_by"] = product_requirement.updated_by
            
        return requirement_dict
    
    def _from_dict(self, document: Dict[str, Any]) -> ProductRequirement:
        """
        Convert a file document to a ProductRequirement.
        
        Args:
            document: The document dictionary.
            
        Returns:
            A ProductRequirement instance.
        """
        # Convert string dates to datetime if needed
        created_at = document.get("created_at")
        updated_at = document.get("updated_at")
        
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                created_at = None
                
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                updated_at = None
        
        # Create ProductRequirement instance
        return ProductRequirement(
            product_requirement_id=document["product_requirement_id"],
            title=document["title"],
            description=document["description"],
            content=document["content"],
            created_by=document["created_by"],
            status=document["status"],
            related_task_id=document["related_task_id"],
            version=document.get("version", 1),
            created_at=created_at,
            updated_at=updated_at,
            updated_by=document.get("updated_by"),
            sections=document.get("sections", []),
            metadata=document.get("metadata", {})
        ) 