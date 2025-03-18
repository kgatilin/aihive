"""
MongoDB implementation of the Product Requirement Repository.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.domain.entities.product_requirement import ProductRequirement

logger = logging.getLogger(__name__)


class MongoDBProductRequirementRepository(ProductRequirementRepositoryInterface):
    """
    MongoDB implementation of the product requirement repository.
    """
    
    def __init__(self, client: AsyncIOMotorClient, database_name: str = "aihive", collection_name: str = "product_requirements"):
        """
        Initialize the MongoDB repository.
        
        Args:
            client: MongoDB client.
            database_name: Name of the database.
            collection_name: Name of the collection.
        """
        self._client = client
        self._db = client[database_name]
        self._collection = self._db[collection_name]
        logger.info(f"Initialized MongoDB product requirement repository with collection {collection_name}")
    
    async def create(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Create a new product requirement.
        
        Args:
            product_requirement: The product requirement to create.
            
        Returns:
            The created product requirement with its ID.
        """
        # Convert dataclass to dict
        requirement_dict = self._to_dict(product_requirement)
        
        # Remove id field for insertion if it's a string ID
        if "product_requirement_id" in requirement_dict and requirement_dict["product_requirement_id"]:
            # Store the original ID
            original_id = requirement_dict["product_requirement_id"]
        else:
            # Generate a new ID
            original_id = str(ObjectId())
            product_requirement.product_requirement_id = original_id
            requirement_dict["product_requirement_id"] = original_id
            
        # Ensure created_at and updated_at are properly set
        now = datetime.utcnow()
        if not requirement_dict.get("created_at"):
            requirement_dict["created_at"] = now
            product_requirement.created_at = now
        if not requirement_dict.get("updated_at"):
            requirement_dict["updated_at"] = now
            product_requirement.updated_at = now
            
        # Insert the document
        await self._collection.insert_one(requirement_dict)
        logger.info(f"Created product requirement with ID {original_id}")
        
        return product_requirement
    
    async def find_by_id(self, product_requirement_id: str) -> Optional[ProductRequirement]:
        """
        Find a product requirement by its ID.
        
        Args:
            product_requirement_id: The ID of the product requirement.
            
        Returns:
            The product requirement if found, None otherwise.
        """
        document = await self._collection.find_one({"product_requirement_id": product_requirement_id})
        if document:
            logger.debug(f"Found product requirement with ID {product_requirement_id}")
            return self._from_dict(document)
        logger.debug(f"Product requirement with ID {product_requirement_id} not found")
        return None
    
    async def update(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Update an existing product requirement.
        
        Args:
            product_requirement: The product requirement to update.
            
        Returns:
            The updated product requirement.
        """
        # Convert dataclass to dict
        requirement_dict = self._to_dict(product_requirement)
        
        # Ensure updated_at is set
        requirement_dict["updated_at"] = datetime.utcnow()
        product_requirement.updated_at = requirement_dict["updated_at"]
        
        # Update the document
        result = await self._collection.update_one(
            {"product_requirement_id": product_requirement.product_requirement_id},
            {"$set": requirement_dict}
        )
        
        if result.matched_count == 0:
            logger.warning(f"No product requirement found with ID {product_requirement.product_requirement_id} for update")
        else:
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
        result = await self._collection.delete_one({"product_requirement_id": product_requirement_id})
        
        if result.deleted_count == 0:
            logger.warning(f"No product requirement found with ID {product_requirement_id} for deletion")
            return False
        
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
        cursor = self._collection.find({"related_task_id": task_id})
        documents = await cursor.to_list(length=None)
        logger.debug(f"Found {len(documents)} product requirements for task ID {task_id}")
        
        return [self._from_dict(doc) for doc in documents]
    
    async def find_by_status(self, status: str) -> List[ProductRequirement]:
        """
        Find product requirements by status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            A list of product requirements with the specified status.
        """
        cursor = self._collection.find({"status": status})
        documents = await cursor.to_list(length=None)
        logger.debug(f"Found {len(documents)} product requirements with status {status}")
        
        return [self._from_dict(doc) for doc in documents]
    
    async def find_by_created_by(self, created_by: str) -> List[ProductRequirement]:
        """
        Find product requirements by creator.
        
        Args:
            created_by: The ID of the creator.
            
        Returns:
            A list of product requirements created by the specified user or agent.
        """
        cursor = self._collection.find({"created_by": created_by})
        documents = await cursor.to_list(length=None)
        logger.debug(f"Found {len(documents)} product requirements created by {created_by}")
        
        return [self._from_dict(doc) for doc in documents]
    
    async def search(self, query: Dict[str, Any]) -> List[ProductRequirement]:
        """
        Search for product requirements based on criteria.
        
        Args:
            query: A dictionary of search criteria.
            
        Returns:
            A list of product requirements matching the criteria.
        """
        cursor = self._collection.find(query)
        documents = await cursor.to_list(length=None)
        logger.debug(f"Found {len(documents)} product requirements matching search criteria")
        
        return [self._from_dict(doc) for doc in documents]
    
    def _to_dict(self, product_requirement: ProductRequirement) -> Dict[str, Any]:
        """
        Convert a ProductRequirement to a dictionary for MongoDB storage.
        
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
            requirement_dict["created_at"] = product_requirement.created_at
        if product_requirement.updated_at:
            requirement_dict["updated_at"] = product_requirement.updated_at
        if product_requirement.updated_by:
            requirement_dict["updated_by"] = product_requirement.updated_by
            
        return requirement_dict
    
    def _from_dict(self, document: Dict[str, Any]) -> ProductRequirement:
        """
        Convert a MongoDB document to a ProductRequirement.
        
        Args:
            document: The MongoDB document.
            
        Returns:
            A ProductRequirement instance.
        """
        # Handle MongoDB ObjectId if present
        if "_id" in document:
            del document["_id"]
            
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
            created_at=document.get("created_at"),
            updated_at=document.get("updated_at"),
            updated_by=document.get("updated_by"),
            sections=document.get("sections", []),
            metadata=document.get("metadata", {})
        ) 