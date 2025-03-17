"""
Interface for the Product Manager Agent.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

from src.task_management.domain.entities.task import Task
from src.product_definition.domain.entities.product_requirement import ProductRequirement


class ProductManagerAgentInterface(ABC):
    """
    Interface for the Product Manager Agent.
    
    The Product Manager Agent is responsible for analyzing user requests,
    determining if clarification is needed, generating clarification questions,
    and creating product requirement documents.
    """
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Get the agent's identifier."""
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> Task:
        """
        Process a task assigned to the Product Manager Agent.
        
        This method will analyze the task, determine if clarification is needed,
        generate clarification questions if necessary, create a product requirement
        document if the information is sufficient, and validate the document.
        
        Args:
            task: The task to process.
            
        Returns:
            The processed task with updated status.
        """
        pass
    
    @abstractmethod
    async def analyze_user_request(self, task: Task) -> Dict[str, Any]:
        """
        Analyze the user request contained in the task.
        
        This method extracts key information from the task, including clarity
        and completeness scores, key features, target audience, and product type.
        
        Args:
            task: The task containing the user request.
            
        Returns:
            A dictionary containing analysis results.
        """
        pass
    
    @abstractmethod
    async def determine_if_clarification_needed(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed based on the analysis.
        
        Args:
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            True if clarification is needed, False otherwise.
        """
        pass
    
    @abstractmethod
    async def generate_clarification_questions(self, task: Task, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate questions for the user based on missing information.
        
        Args:
            task: The task containing the user request.
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            A list of questions for the user.
        """
        pass
    
    @abstractmethod
    async def create_product_requirement_document(self, task: Task, analysis: Dict[str, Any]) -> ProductRequirement:
        """
        Create a product requirement document based on the analysis.
        
        Args:
            task: The task containing the user request.
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            The created product requirement document.
        """
        pass
    
    @abstractmethod
    async def validate_product_requirement_document(self, prd: ProductRequirement) -> bool:
        """
        Validate that the PRD meets quality standards.
        
        Args:
            prd: The product requirement document to validate.
            
        Returns:
            True if the PRD is valid, False otherwise.
        """
        pass 