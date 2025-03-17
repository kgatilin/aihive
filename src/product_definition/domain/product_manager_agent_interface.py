"""
This module defines the interface for the Product Manager Agent in the Product Definition domain.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.task_management.domain.entities.task import Task


class ProductManagerAgentInterface(ABC):
    """
    Interface defining the responsibilities of the Product Manager Agent.
    The Product Manager Agent is responsible for analyzing user requests and 
    creating product requirement documents.
    """
    
    @abstractmethod
    async def process_task(self, task: Task) -> Task:
        """
        Process a task assigned to the Product Manager Agent.
        This is the main entry point for task processing.
        
        Args:
            task: The task to process
            
        Returns:
            The updated task after processing
        """
        pass
    
    @abstractmethod
    async def analyze_user_request(self, task: Task) -> Dict[str, Any]:
        """
        Analyze the user request contained in the task and extract key information.
        
        Args:
            task: The task containing the user request
            
        Returns:
            A dictionary containing the analyzed information
        """
        pass
    
    @abstractmethod
    async def determine_if_clarification_needed(self, task: Task, analysis: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed from the user based on the analysis.
        
        Args:
            task: The task being processed
            analysis: The analysis of the user request
            
        Returns:
            True if clarification is needed, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_clarification_questions(self, task: Task, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate clarification questions for the user based on the analysis.
        
        Args:
            task: The task being processed
            analysis: The analysis of the user request
            
        Returns:
            A list of clarification questions
        """
        pass
    
    @abstractmethod
    async def process_clarification_response(self, task: Task, response: str) -> Dict[str, Any]:
        """
        Process a clarification response from the user.
        
        Args:
            task: The task being processed
            response: The user's response to the clarification questions
            
        Returns:
            Updated analysis based on the clarification
        """
        pass
    
    @abstractmethod
    async def create_product_requirement_document(self, task: Task, analysis: Dict[str, Any]) -> str:
        """
        Create a product requirement document based on the analysis.
        
        Args:
            task: The task being processed
            analysis: The analysis of the user request
            
        Returns:
            The PRD content as a string
        """
        pass
    
    @abstractmethod
    async def validate_product_requirement_document(self, prd_content: str) -> bool:
        """
        Validate that the PRD meets quality standards.
        
        Args:
            prd_content: The content of the PRD
            
        Returns:
            True if the PRD is valid, False otherwise
        """
        pass 