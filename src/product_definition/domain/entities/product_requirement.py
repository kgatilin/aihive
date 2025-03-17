"""
Product Requirement entity representing a Product Requirement Document (PRD).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ProductRequirement:
    """
    Represents a Product Requirement Document (PRD).
    
    A PRD outlines the features, functionality, and purpose of a product
    or feature that needs to be built.
    """
    
    product_requirement_id: str
    title: str
    description: str
    content: str
    created_by: str
    status: str  # draft, review, approved, rejected
    related_task_id: str
    
    # Optional fields
    version: int = 1
    created_at: datetime = None
    updated_at: datetime = None
    updated_by: Optional[str] = None
    sections: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.sections is None:
            self.sections = []
        if self.metadata is None:
            self.metadata = {}
    
    def update_content(self, content: str, updated_by: str) -> None:
        """
        Update the content of the product requirement.
        
        Args:
            content: The new content.
            updated_by: The ID of the user or agent updating the content.
        """
        self.content = content
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        self.version += 1
    
    def update_status(self, status: str, updated_by: str) -> None:
        """
        Update the status of the product requirement.
        
        Args:
            status: The new status (draft, review, approved, rejected).
            updated_by: The ID of the user or agent updating the status.
        """
        if status not in ["draft", "review", "approved", "rejected"]:
            raise ValueError(f"Invalid status: {status}")
        
        self.status = status
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update metadata.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def extract_sections(self) -> List[str]:
        """
        Extract section titles from the content.
        
        Returns:
            A list of section titles.
        """
        import re
        # Look for markdown headings (## Section Title)
        sections = re.findall(r'^##\s+(.+)$', self.content, re.MULTILINE)
        self.sections = sections
        return sections 