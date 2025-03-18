"""
Product Manager Agent implementation.

This agent is responsible for analyzing user requests, determining if clarification
is needed, generating clarification questions, and creating product requirement documents.
"""

import logging
import traceback
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel

from src.task_management.domain.entities.task import Task
from src.task_management.application.task_service import TaskService
from src.task_management.domain.value_objects.task_status import TaskStatus

from src.product_definition.domain.entities.product_requirement import ProductRequirement
from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.domain.interfaces.product_manager_agent_interface import ProductManagerAgentInterface

from src.core.agent.ai_agent import AIAgent
from src.core.agent.agent_tool_interface import AgentToolInterface
from src.core.config import Config
from src.core.exceptions import InvalidOperationError
from src.core.prompt_manager import PromptManager, get_prompt_manager

logger = logging.getLogger(__name__)


class ProductManagerAgent(AIAgent, ProductManagerAgentInterface):
    """
    Product Manager Agent implementation.
    
    This agent analyzes user requests for product features, determines if the request
    contains sufficient information, asks clarifying questions if needed, and creates
    product requirement documents based on the analysis.
    """
    
    def __init__(
        self,
        task_service: TaskService,
        product_requirement_repository: ProductRequirementRepositoryInterface,
        tool_registry: Optional[Dict[str, AgentToolInterface]] = None,
        model_name: Optional[str] = None,
        llm: Optional[BaseChatModel] = None,
        config: Optional[Config] = None,
        prompt_manager = None
    ):
        """
        Initialize the Product Manager Agent.
        
        Args:
            task_service: The task service for interacting with tasks.
            product_requirement_repository: The repository for product requirements.
            tool_registry: The registry for agent tools.
            model_name: The LLM model to use.
            llm: Optional LLM instance for testing.
            config: Optional configuration.
            prompt_manager: Optional prompt manager for testing.
        """
        super().__init__(
            agent_id="product_manager",
            name="Product Manager Agent",
            description="Analyzes product requirements and creates PRDs",
            tool_registry=tool_registry,
            model_name=model_name,
            llm=llm,
            config=config
        )
        
        self.task_service = task_service
        self.product_requirement_repository = product_requirement_repository
        self._prompt_manager = prompt_manager or (config.prompt_manager if config else get_prompt_manager())
    
    def _setup_prompt(self) -> str:
        """Set up the base prompt for the Product Manager Agent."""
        return """
        You are an experienced Product Manager tasked with analyzing product requirements and creating comprehensive Product Requirement Documents (PRDs).
        
        Your objective is to:
        1. Analyze user requests and task descriptions
        2. Assess clarity and completeness
        3. Generate clarification questions when needed
        4. Create well-structured PRDs when requirements are clear
        
        Please provide structured, detailed responses in JSON format.
        """
    
    def _extract_metadata_from_tags(self, task: Task) -> Dict[str, Any]:
        """Extract metadata from task tags.
        
        Args:
            task: The task to extract metadata from
        
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        if not task.tags:
            return metadata
            
        for tag in task.tags:
            if ":" in tag:
                key, value = tag.split(":", 1)
                metadata[key] = value
                
        return metadata
    
    def _extract_metadata_from_description(self, description: str) -> Dict[str, Any]:
        """Extract metadata from task description content.
        
        Args:
            description: The task description to extract metadata from
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        
        # Look for structured data in the description
        # Example: "Product Type: Mobile App" or "Target Audience: Enterprise Users"
        if not description:
            return metadata
            
        lines = description.split("\n")
        for line in lines:
            if ":" in line:
                # Try to extract key-value pairs
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(" ", "_")
                    value = parts[1].strip()
                    metadata[key] = value
                    
        return metadata
    
    async def analyze_user_request(self, task: Task) -> Dict[str, Any]:
        """Analyze a user request to determine clarity and completeness.
        
        Args:
            task: The task containing the user request
            
        Returns:
            Analysis results including clarity score, completeness score,
            key features, target audience, product type, and missing information
        """
        # Extract metadata from tags and description to provide context
        tag_metadata = self._extract_metadata_from_tags(task)
        desc_metadata = self._extract_metadata_from_description(task.description)
        
        # Combine metadata with task information
        input_data = {
            "title": task.title,
            "description": task.description,
            "tags": task.tags,
            "metadata": {**tag_metadata, **desc_metadata}
        }
        
        try:
            # Get the prompt from the prompt manager
            prompt = self._prompt_manager.format_prompt(
                "product_manager_agent", 
                "analyze_user_request",
                input_data
            )
            
            # Invoke the LLM to analyze the request
            result = await self.invoke_llm(prompt, input_data)
            
            # Ensure the required fields are present in the result
            required_fields = ["clarity_score", "completeness_score", "key_features", 
                               "target_audience", "product_type", "missing_information"]
            
            for field in required_fields:
                if field not in result:
                    result[field] = [] if field == "key_features" or field == "missing_information" else "unknown"
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing user request: {e}")
            # Return a default analysis if the LLM fails
            return {
                "clarity_score": 1.0,
                "completeness_score": 1.0,
                "key_features": [],
                "target_audience": "unknown",
                "product_type": "unknown",
                "missing_information": ["Error analyzing request"]
            }
    
    async def generate_clarification_questions(self, task: Task, analysis: Dict[str, Any]) -> List[str]:
        """Generate questions to clarify missing or incomplete information.
        
        Args:
            task: The task to generate questions for
            analysis: The analysis results from analyze_user_request
            
        Returns:
            List of clarification questions
        """
        # Don't generate questions if the analysis is clear and complete
        if (analysis.get("clarity_score", 0) >= 7.0 and 
            analysis.get("completeness_score", 0) >= 7.0 and
            not analysis.get("missing_information")):
            return []
        
        # Prepare input data for the prompt
        input_data = {
            "title": task.title,
            "description": task.description,
            **analysis
        }
        
        try:
            # Get the prompt from the prompt manager
            prompt = self._prompt_manager.format_prompt(
                "product_manager_agent", 
                "generate_clarification_questions",
                input_data
            )
            
            # Invoke the LLM to generate questions
            result = await self.invoke_llm(prompt, input_data)
            
            # Parse the questions from the result
            if isinstance(result, list):
                questions = result
            elif isinstance(result, dict) and "text" in result:
                # Try to parse the text as JSON
                try:
                    questions = json.loads(result["text"])
                except json.JSONDecodeError:
                    # Split by newlines and clean up
                    questions = [q.strip() for q in result["text"].split("\n") if q.strip()]
            else:
                questions = []
            
            return questions
        except Exception as e:
            logger.error(f"Error generating clarification questions: {e}")
            # Generate some generic questions based on the missing information
            generic_questions = []
            for missing in analysis.get("missing_information", []):
                generic_questions.append(f"Could you provide more details about the {missing}?")
            
            if not generic_questions:
                generic_questions = [
                    "Could you clarify the target audience for this product?",
                    "What are the key features you expect to be implemented?",
                    "What problem does this product aim to solve?"
                ]
            
            return generic_questions
    
    async def create_product_requirement_document(self, task: Task, analysis: Dict[str, Any]) -> ProductRequirement:
        """Create a Product Requirement Document (PRD) based on task and analysis.
        
        Args:
            task: The task containing the request information
            analysis: The analysis of the request
            
        Returns:
            The created product requirement document
        """
        try:
            # Extract important information from the analysis
            target_audience = analysis.get("target_audience", "Not specified")
            key_features = analysis.get("key_features", [])
            product_type = analysis.get("product_type", "Not specified")
            
            # Prepare input data for the prompt
            input_data = {
                "title": task.title,
                "description": task.description,
                "target_audience": target_audience,
                "product_type": product_type,
                "key_features": ", ".join(key_features) if key_features else "Not specified"
            }
            
            # Get the prompt from the prompt manager
            prompt = self._prompt_manager.format_prompt(
                "product_manager_agent", 
                "create_product_requirement_document",
                input_data
            )
            
            # Generate the PRD content using the LLM
            result = await self.invoke_llm(prompt, input_data)
            
            # If the result is a dictionary with a 'text' key, extract it
            content = result.get("text", "") if isinstance(result, dict) else str(result)
            
            # Create a title for the PRD
            title = f"{task.title} - Product Requirement Document"
            
            # Create a product requirement with a unique ID
            product_requirement_id = f"prd-{task.task_id}"
            
            prd = ProductRequirement(
                product_requirement_id=product_requirement_id,
                title=title,
                description=f"PRD for {task.title}",
                content=content,
                created_by=self.agent_id,
                status="draft",
                related_task_id=task.task_id,
                metadata={
                    "analysis": analysis,
                    "created_at": datetime.now().isoformat(),
                    "created_by": self.agent_id
                }
            )
            
            # Save the PRD to the repository
            saved_prd = self.product_requirement_repository.create(prd)
            logger.info(f"Created PRD {saved_prd.product_requirement_id} for task {task.task_id}")
            
            return saved_prd
            
        except Exception as e:
            logger.error(f"Error creating PRD: {e}")
            # Re-raise the exception to be handled by the caller
            raise
    
    async def validate_product_requirement_document(self, prd: ProductRequirement) -> bool:
        """Validate a Product Requirement Document.
        
        Args:
            prd: The product requirement document to validate
            
        Returns:
            True if the document is valid, False otherwise
        """
        try:
            # Prepare input data for the prompt
            input_data = {
                "title": prd.title,
                "content": prd.content
            }
            
            # Get the prompt from the prompt manager
            prompt = self._prompt_manager.format_prompt(
                "product_manager_agent", 
                "validate_product_requirement_document",
                input_data
            )
            
            # Validate the PRD using the LLM
            validation_result = await self.invoke_llm(prompt, input_data)
            
            # Check if validation was successful
            is_valid = validation_result.get("is_valid", False) if isinstance(validation_result, dict) else False
            
            # Log validation results
            logger.info(f"Validated PRD {prd.product_requirement_id}: valid={is_valid}")
            if not is_valid and isinstance(validation_result, dict):
                missing = validation_result.get("missing_sections", [])
                weak = validation_result.get("weak_sections", [])
                score = validation_result.get("score", 0)
                logger.info(f"PRD validation score: {score}/10")
                logger.info(f"Missing sections: {missing}")
                logger.info(f"Weak sections: {weak}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating PRD: {e}")
            # Return False on error to indicate validation failure
            return False
    
    async def process_task(self, task: Task) -> Task:
        """Process a task to analyze requirements and potentially create a PRD.
        
        Args:
            task: The task to process
            
        Returns:
            The updated task
        """
        # Store the original task_id for error handling
        task_id = task.task_id
        
        # Verify the task is valid for processing
        if not task_id or not task.title:
            raise InvalidOperationError("Task missing required fields")
        
        # Update task status to IN_PROGRESS
        logger.info(f"Processing task {task_id}: {task.title}")
        task = await self.task_service.update_task_status(task_id, TaskStatus.IN_PROGRESS.value)
        
        try:
            # Step 1: Analyze the user request
            analysis = await self.analyze_user_request(task)
            
            # Step 2: Check if clarification is needed
            if (analysis.get("clarity_score", 0) < 7.0 or
                analysis.get("completeness_score", 0) < 7.0 or
                analysis.get("missing_information")):
                
                # Generate clarification questions
                questions = await self.generate_clarification_questions(task, analysis)
                
                if questions:
                    # Add questions as a comment on the task
                    questions_text = "\n".join([f"- {q}" for q in questions])
                    comment = (f"Clarity Score: {analysis.get('clarity_score', 'N/A')}/10\n"
                              f"Completeness Score: {analysis.get('completeness_score', 'N/A')}/10\n\n"
                              f"I need more information to create a comprehensive PRD. "
                              f"Please provide answers to the following questions:\n\n{questions_text}")
                    
                    await self.task_service.add_comment(task_id, comment)
                    
                    # Update task status to BLOCKED
                    task = await self.task_service.update_task_status(task_id, TaskStatus.BLOCKED.value)
                    return task
            
            # Step 3: Create PRD if sufficient information is available
            prd = await self.create_product_requirement_document(task, analysis)
            
            # Step 4: Validate the PRD
            is_valid = await self.validate_product_requirement_document(prd)
            
            if is_valid:
                # Add PRD reference as a comment on the task
                comment = (f"Created Product Requirement Document: {prd.title}\n"
                          f"PRD ID: {prd.product_requirement_id}\n\n"
                          f"The PRD has been saved and can be accessed through the Product Requirements repository.")
                
                await self.task_service.add_comment(task_id, comment)
                
                # Update task status to COMPLETED
                task = await self.task_service.update_task_status(task_id, TaskStatus.COMPLETED.value)
            else:
                # Add comment about invalid PRD
                comment = (f"Created initial Product Requirement Document, but it requires revision.\n"
                          f"PRD ID: {prd.product_requirement_id}\n\n"
                          f"Please review and provide additional information to improve the PRD quality.")
                
                await self.task_service.add_comment(task_id, comment)
                
                # Update task status to BLOCKED
                task = await self.task_service.update_task_status(task_id, TaskStatus.BLOCKED.value)
            
            return task
                
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            
            # Add error comment
            try:
                await self.task_service.add_comment(
                    task_id=task_id,
                    comment=f"An error occurred while processing this task: {str(e)}",
                    created_by=self.agent_id
                )
                
                # Update task status to ERROR
                task = await self.task_service.update_task_status(
                    task_id=task_id,
                    new_status=TaskStatus.ERROR.value,
                    changed_by=self.agent_id,
                    reason=f"Error processing task: {str(e)}"
                )
            except Exception as ex:
                logger.error(f"Error updating task status after exception: {ex}")
            
            # Re-raise the exception if we couldn't update the task status
            return task
    
    async def determine_if_clarification_needed(self, analysis: Dict[str, Any]) -> bool:
        """Determine if clarification is needed based on the analysis results.
        
        Args:
            analysis: The analysis results from analyze_user_request
            
        Returns:
            True if clarification is needed, False otherwise
        """
        # Clarification is needed if:
        # - The clarity score is below 7.0
        # - The completeness score is below 7.0
        # - There is missing critical information
        
        has_missing_info = len(analysis.get("missing_information", [])) > 0
        
        is_clear_enough = analysis.get("clarity_score", 0) >= 7.0
        is_complete_enough = analysis.get("completeness_score", 0) >= 7.0
        
        return not (is_clear_enough and is_complete_enough) or has_missing_info 