"""
Repository for storing and retrieving product requirements.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.product_definition.models.product_requirement import ProductRequirement

logger = logging.getLogger(__name__)


class ProductRequirementRepository:
    """
    Repository for product requirements.
    """
    
    def __init__(self):
        """Initialize the repository."""
        self._product_requirements = {}  # In-memory storage for demo purposes
    
    def create(self, product_requirement: ProductRequirement) -> ProductRequirement:
        """
        Create a new product requirement.
        
        Args:
            product_requirement: The product requirement to create
            
        Returns:
            The created product requirement
        """
        if product_requirement.product_requirement_id in self._product_requirements:
            raise ValueError(
                f"Product requirement with ID {product_requirement.product_requirement_id} already exists"
            )
        
        self._product_requirements[product_requirement.product_requirement_id] = product_requirement
        logger.info(
            f"Created product requirement {product_requirement.product_requirement_id}: {product_requirement.title}"
        )
        return product_requirement
    
    def get(self, product_requirement_id: str) -> Optional[ProductRequirement]:
        """
        Get a product requirement by ID.
        
        Args:
            product_requirement_id: The ID of the product requirement to get
            
        Returns:
            The product requirement if found, None otherwise
        """
        return self._product_requirements.get(product_requirement_id)
    
    def update(self, product_requirement_id: str, updates: Dict[str, Any]) -> Optional[ProductRequirement]:
        """
        Update a product requirement.
        
        Args:
            product_requirement_id: The ID of the product requirement to update
            updates: Dictionary of fields to update
            
        Returns:
            The updated product requirement if found, None otherwise
        """
        product_requirement = self.get(product_requirement_id)
        if not product_requirement:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(product_requirement, key):
                setattr(product_requirement, key, value)
        
        product_requirement.updated_at = datetime.now()
        logger.info(f"Updated product requirement {product_requirement_id}")
        return product_requirement
    
    def delete(self, product_requirement_id: str) -> bool:
        """
        Delete a product requirement.
        
        Args:
            product_requirement_id: The ID of the product requirement to delete
            
        Returns:
            True if the product requirement was deleted, False otherwise
        """
        if product_requirement_id in self._product_requirements:
            del self._product_requirements[product_requirement_id]
            logger.info(f"Deleted product requirement {product_requirement_id}")
            return True
        return False
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ProductRequirement]:
        """
        List product requirements with optional filtering.
        
        Args:
            filters: Optional dictionary of filters to apply
            
        Returns:
            List of product requirements matching the filters
        """
        product_requirements = list(self._product_requirements.values())
        
        if not filters:
            return product_requirements
        
        # Apply filters
        filtered_product_requirements = []
        for product_requirement in product_requirements:
            match = True
            for key, value in filters.items():
                if hasattr(product_requirement, key):
                    requirement_value = getattr(product_requirement, key)
                    if requirement_value != value:
                        match = False
                        break
            
            if match:
                filtered_product_requirements.append(product_requirement)
        
        return filtered_product_requirements
    
    def find_by_task_id(self, task_id: str) -> List[ProductRequirement]:
        """
        Find product requirements by related task ID.
        
        Args:
            task_id: The ID of the related task
            
        Returns:
            List of product requirements related to the task
        """
        return self.list({"related_task_id": task_id}) 