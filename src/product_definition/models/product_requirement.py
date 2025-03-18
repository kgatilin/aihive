"""
Product requirement models.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


class ProductRequirement:
    """
    Product Requirement Document (PRD) entity.
    """
    
    def __init__(
        self,
        product_requirement_id: str,
        title: str,
        description: str,
        content: str,
        created_by: str,
        status: str = "draft",
        related_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a ProductRequirement.
        
        Args:
            product_requirement_id: Unique identifier for the product requirement
            title: Title of the product requirement
            description: Brief description of the product requirement
            content: Full content of the product requirement document
            created_by: ID of the user or agent who created the document
            status: Status of the document (draft, review, approved, etc.)
            related_task_id: ID of the related task, if any
            metadata: Additional metadata for the document
            created_at: When the document was created
            updated_at: When the document was last updated
        """
        self.product_requirement_id = product_requirement_id
        self.title = title
        self.description = description
        self.content = content
        self.created_by = created_by
        self.status = status
        self.related_task_id = related_task_id
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.sections = self.extract_sections()
    
    def extract_sections(self) -> Dict[str, str]:
        """
        Extract sections from the document content.
        
        Returns:
            Dictionary of section titles and their content
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in self.content.split('\n'):
            # Check for Markdown headings (# or ## or ### etc.)
            if line.startswith('#'):
                # If we've been collecting content for a section, save it
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start a new section
                heading_level = 0
                for char in line:
                    if char == '#':
                        heading_level += 1
                    else:
                        break
                
                current_section = line[heading_level:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def update_section(self, section_title: str, content: str) -> None:
        """
        Update a section in the document.
        
        Args:
            section_title: The title of the section to update
            content: The new content for the section
        """
        # Check if the section exists
        matching_sections = [s for s in self.sections.keys() if s.lower() == section_title.lower()]
        
        if matching_sections:
            # Update existing section
            exact_title = matching_sections[0]
            self.sections[exact_title] = content
            
            # Regenerate full content
            self._regenerate_content()
        else:
            # Add new section
            self.sections[section_title] = content
            
            # Add to full content
            self.content += f"\n\n## {section_title}\n{content}"
        
        self.updated_at = datetime.now()
    
    def _regenerate_content(self) -> None:
        """Regenerate the full content from sections."""
        content_parts = []
        
        for title, section_content in self.sections.items():
            # Determine heading level (default to ##)
            heading_level = "##"
            if title.startswith("#"):
                # The title already includes heading markers
                content_parts.append(f"{title}\n{section_content}")
            else:
                content_parts.append(f"{heading_level} {title}\n{section_content}")
        
        self.content = "\n\n".join(content_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the product requirement to a dictionary.
        
        Returns:
            Dictionary representation of the product requirement
        """
        return {
            'product_requirement_id': self.product_requirement_id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'created_by': self.created_by,
            'status': self.status,
            'related_task_id': self.related_task_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'sections': self.sections
        } 