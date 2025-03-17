"""
Interface for the Product Requirement Repository.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from src.product_definition.domain.entities.product_requirement import ProductRequirement


class ProductRequirementRepositoryInterface(ABC):
    """
    Interface for repositories that manage Product Requirement Documents.
    """
    
    @abstractmethod
    async def create(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Create a new product requirement.
        
        Args:
            product_requirement: The product requirement to create.
            
        Returns:
            The created product requirement with its ID.
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, product_requirement_id: str) -> Optional[ProductRequirement]:
        """
        Find a product requirement by its ID.
        
        Args:
            product_requirement_id: The ID of the product requirement.
            
        Returns:
            The product requirement if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def update(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Update an existing product requirement.
        
        Args:
            product_requirement: The product requirement to update.
            
        Returns:
            The updated product requirement.
        """
        pass
    
    @abstractmethod
    async def delete(self, product_requirement_id: str) -> bool:
        """
        Delete a product requirement.
        
        Args:
            product_requirement_id: The ID of the product requirement to delete.
            
        Returns:
            True if the product requirement was deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    async def find_by_task_id(self, task_id: str) -> List[ProductRequirement]:
        """
        Find product requirements related to a task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            A list of product requirements related to the task.
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[ProductRequirement]:
        """
        Find product requirements by status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            A list of product requirements with the specified status.
        """
        pass
    
    @abstractmethod
    async def find_by_created_by(self, created_by: str) -> List[ProductRequirement]:
        """
        Find product requirements by creator.
        
        Args:
            created_by: The ID of the creator.
            
        Returns:
            A list of product requirements created by the specified user or agent.
        """
        pass
    
    @abstractmethod
    async def search(self, query: Dict[str, Any]) -> List[ProductRequirement]:
        """
        Search for product requirements based on criteria.
        
        Args:
            query: A dictionary of search criteria.
            
        Returns:
            A list of product requirements matching the criteria.
        """
        pass 