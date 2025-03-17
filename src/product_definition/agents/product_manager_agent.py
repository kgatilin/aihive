"""
Product Manager Agent implementation.

This agent is responsible for analyzing user requests, determining if clarification
is needed, generating clarification questions, and creating product requirement documents.
"""

import logging
import traceback
from typing import Dict, List, Any, Optional

from src.task_management.domain.entities.task import Task
from src.task_management.application.task_service import TaskService
from src.task_management.domain.value_objects.task_status import TaskStatus

from src.product_definition.domain.entities.product_requirement import ProductRequirement
from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.product_definition.domain.interfaces.product_manager_agent_interface import ProductManagerAgentInterface

from src.core.agent.tool_registry import ToolRegistry


logger = logging.getLogger(__name__)


class ProductManagerAgent(ProductManagerAgentInterface):
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
        tool_registry: ToolRegistry,
        agent_id: str = "pma-agent"
    ):
        """
        Initialize the Product Manager Agent.
        
        Args:
            task_service: The task service for interacting with tasks.
            product_requirement_repository: The repository for product requirements.
            tool_registry: The registry of tools available to the agent.
            agent_id: The ID of the agent.
        """
        self._task_service = task_service
        self._product_requirement_repository = product_requirement_repository
        self._tool_registry = tool_registry
        self._agent_id = agent_id
    
    @property
    def agent_id(self) -> str:
        """Get the agent's identifier."""
        return self._agent_id
    
    async def process_task(self, task: Task) -> Task:
        """
        Process a task assigned to the Product Manager Agent.
        
        This method will update the task status, analyze the user request,
        determine if clarification is needed, generate clarification questions
        if necessary, create a product requirement document if the information
        is sufficient, and validate the document.
        
        Args:
            task: The task to process.
            
        Returns:
            The processed task with updated status.
        """
        logger.info(f"Processing task {task.task_id}: {task.title}")
        
        try:
            # Update task status to in progress
            task = await self._task_service.update_task_status(
                task_id=task.task_id,
                new_status=TaskStatus.IN_PROGRESS.value,
                changed_by=self.agent_id,
                reason="Starting to analyze request"
            )
            
            # Analyze the user request
            analysis = await self.analyze_user_request(task)
            logger.info(f"Analysis for task {task.task_id}: {analysis}")
            
            # Determine if clarification is needed
            if await self.determine_if_clarification_needed(analysis):
                # Generate clarification questions
                questions = await self.generate_clarification_questions(task, analysis)
                logger.info(f"Clarification needed for task {task.task_id}. Questions: {questions}")
                
                # Update task status to blocked (need clarification)
                task = await self._task_service.update_task_status(
                    task_id=task.task_id,
                    new_status=TaskStatus.BLOCKED.value,
                    changed_by=self.agent_id,
                    reason="Additional information needed to create PRD"
                )
                
                # Add clarification questions as a comment
                comment_text = "Please provide clarification on the following:\n"
                for i, question in enumerate(questions, 1):
                    comment_text += f"{i}. {question}\n"
                
                await self._task_service.add_comment(
                    task_id=task.task_id,
                    comment=comment_text.strip(),
                    created_by=self.agent_id
                )
            else:
                # Create product requirement document
                prd = await self.create_product_requirement_document(task, analysis)
                logger.info(f"Created PRD for task {task.task_id}: {prd.title}")
                
                # Validate the PRD
                is_valid = await self.validate_product_requirement_document(prd)
                
                if is_valid:
                    # Save the PRD
                    saved_prd = await self._product_requirement_repository.create(prd)
                    logger.info(f"Saved PRD with ID {saved_prd.product_requirement_id}")
                    
                    # Update task status to completed
                    task = await self._task_service.update_task_status(
                        task_id=task.task_id,
                        new_status=TaskStatus.COMPLETED.value,
                        changed_by=self.agent_id,
                        reason="Product requirement document created successfully"
                    )
                    
                    # Add a comment with the PRD info
                    await self._task_service.add_comment(
                        task_id=task.task_id,
                        comment=f"Created PRD: {saved_prd.title} (ID: {saved_prd.product_requirement_id})",
                        created_by=self.agent_id
                    )
                else:
                    # Update task status to review (needs revision)
                    task = await self._task_service.update_task_status(
                        task_id=task.task_id,
                        new_status=TaskStatus.REVIEW.value,
                        changed_by=self.agent_id,
                        reason="Created PRD does not meet quality standards"
                    )
                    
                    # Add a comment explaining the issue
                    await self._task_service.add_comment(
                        task_id=task.task_id,
                        comment="The PRD created doesn't meet quality standards. Manual revision needed.",
                        created_by=self.agent_id
                    )
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Update task status to failed
            task = await self._task_service.update_task_status(
                task_id=task.task_id,
                new_status=TaskStatus.CANCELED.value,  # Use CANCELED for failed tasks
                changed_by=self.agent_id,
                reason=f"Error processing task: {str(e)}"
            )
            
            # Add a comment with the error details
            await self._task_service.add_comment(
                task_id=task.task_id,
                comment=f"An error occurred while processing this task: {str(e)}",
                created_by=self.agent_id
            )
        
        return task
    
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
        # In a real implementation, this might use an LLM to analyze the request
        # For simplicity, we'll extract some basic information and assign scores
        
        analysis = {
            "clarity_score": 0.0,
            "completeness_score": 0.0,
            "key_features": [],
            "target_audience": "unknown",
            "product_type": "unknown",
            "missing_information": []
        }
        
        # Extract metadata from task tags if available
        if hasattr(task, 'tags') and task.tags:
            for tag in task.tags:
                if ":" in tag:
                    key, value = tag.split(":", 1)
                    analysis[key] = value
        
        # Process the description to extract features and metadata
        description = task.description.lower()
        
        # Look for key phrases indicating features
        feature_indicators = ["feature:", "add", "implement", "create", "develop", "build"]
        lines = description.split("\n")
        
        for line in lines:
            if any(indicator in line.lower() for indicator in feature_indicators):
                analysis["key_features"].append(line.strip())
            
            # Look for metadata in the description
            if "target audience:" in line.lower() and analysis["target_audience"] == "unknown":
                parts = line.lower().split("target audience:", 1)
                if len(parts) > 1:
                    analysis["target_audience"] = parts[1].strip()
            
            if "product type:" in line.lower() and analysis["product_type"] == "unknown":
                parts = line.lower().split("product type:", 1)
                if len(parts) > 1:
                    analysis["product_type"] = parts[1].strip()
        
        # Determine clarity based on description length and key features
        if len(description) > 100 and analysis["key_features"]:
            analysis["clarity_score"] = min(8.5, 5.0 + len(analysis["key_features"]) * 0.5)
        else:
            analysis["clarity_score"] = min(5.0, 3.0 + len(description) * 0.01)
        
        # Determine completeness based on available information
        completeness_factors = [
            analysis["target_audience"] != "unknown",
            analysis["product_type"] != "unknown",
            len(analysis["key_features"]) > 0,
            "estimated_effort" in analysis,
            "priority" in analysis
        ]
        
        analysis["completeness_score"] = sum(1.5 for factor in completeness_factors if factor) + 2.0
        
        # Identify missing information
        if analysis["target_audience"] == "unknown":
            analysis["missing_information"].append("target_audience")
        if analysis["product_type"] == "unknown":
            analysis["missing_information"].append("product_type")
        if not analysis["key_features"]:
            analysis["missing_information"].append("key_features")
        if "success_metrics" not in analysis:
            analysis["missing_information"].append("success_metrics")
        if "constraints" not in analysis:
            analysis["missing_information"].append("constraints")
        
        return analysis
    
    async def determine_if_clarification_needed(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if clarification is needed based on the analysis.
        
        Args:
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            True if clarification is needed, False otherwise.
        """
        # Clarification is needed if:
        # - The clarity score is below 5.0
        # - The completeness score is below 5.0
        # - There are missing critical information points
        
        critical_missing = ["target_audience", "key_features"]
        has_critical_missing = any(item in analysis.get("missing_information", []) for item in critical_missing)
        
        return (
            analysis["clarity_score"] < 5.0 or
            analysis["completeness_score"] < 5.0 or
            has_critical_missing
        )
    
    async def generate_clarification_questions(self, task: Task, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate questions for the user based on missing information.
        
        Args:
            task: The task containing the user request.
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            A list of questions for the user.
        """
        questions = []
        
        # Generate questions based on missing information
        if "target_audience" in analysis.get("missing_information", []):
            questions.append("Who is the target audience for this product/feature?")
        
        if "key_features" in analysis.get("missing_information", []):
            questions.append("What specific features should be included in this product?")
        
        if "product_type" in analysis.get("missing_information", []):
            questions.append("What type of product is this (web app, mobile app, desktop app, API, etc.)?")
        
        if "success_metrics" in analysis.get("missing_information", []):
            questions.append("What metrics should be used to measure the success of this product/feature?")
        
        if "constraints" in analysis.get("missing_information", []):
            questions.append("Are there any technical or business constraints that should be considered?")
        
        # Add additional clarification questions based on the task description
        if analysis["clarity_score"] < 5.0:
            questions.append("Could you provide more details about the purpose of this product/feature?")
        
        if "estimated_effort" not in analysis:
            questions.append("What is the expected timeline or effort level for this product/feature?")
        
        return questions
    
    async def create_product_requirement_document(self, task: Task, analysis: Dict[str, Any]) -> ProductRequirement:
        """
        Create a product requirement document based on the analysis.
        
        Args:
            task: The task containing the user request.
            analysis: The analysis results from analyze_user_request.
            
        Returns:
            The created product requirement document.
        """
        # In a real implementation, this might use an LLM to generate a PRD
        # For simplicity, we'll create a basic PRD with the available information
        
        # Generate a title based on the task title
        title = f"PRD: {task.title}"
        
        # Generate the PRD content
        content = f"""# {title}

## Overview
{task.description}

## Background
This PRD was created based on the task with ID {task.task_id}.

## Target Audience
{analysis.get("target_audience", "Not specified")}

## Product Type
{analysis.get("product_type", "Not specified")}

## Key Features
"""
        
        # Add key features
        for feature in analysis.get("key_features", []):
            content += f"- {feature}\n"
        
        if not analysis.get("key_features"):
            content += "- No features specified\n"
        
        # Add additional sections
        content += """
## User Needs
- To be determined based on further analysis

## Success Metrics
- To be determined based on further analysis

## Implementation Constraints
- To be determined based on further analysis

## Timeline
- To be determined based on further analysis
"""
        
        # Create the product requirement entity
        prd = ProductRequirement(
            product_requirement_id=f"prd-{task.task_id}",
            title=title,
            description=f"PRD for {task.title}",
            content=content,
            created_by=self.agent_id,
            status="draft",
            related_task_id=task.task_id,
            metadata={
                "task_priority": task.priority.value if hasattr(task, 'priority') else None,
                "analysis_clarity_score": analysis["clarity_score"],
                "analysis_completeness_score": analysis["completeness_score"]
            }
        )
        
        # Extract sections
        prd.extract_sections()
        
        return prd
    
    async def validate_product_requirement_document(self, prd: ProductRequirement) -> bool:
        """
        Validate that the PRD meets quality standards.
        
        Args:
            prd: The product requirement document to validate.
            
        Returns:
            True if the PRD is valid, False otherwise.
        """
        # In a real implementation, this might use more sophisticated validation
        # For simplicity, we'll check for basic requirements
        
        # Check that the PRD has a title and content
        if not prd.title or not prd.content:
            return False
        
        # Check that the content has some minimum length
        if len(prd.content) < 100:
            return False
        
        # Check that the PRD has sections
        sections = prd.sections or prd.extract_sections()
        if not sections or len(sections) < 3:
            return False
        
        # Check for specific required sections
        required_sections = ["Overview", "Key Features", "User Needs", "Success Metrics"]
        section_titles = [section.lower() for section in sections]
        
        for required in required_sections:
            if not any(required.lower() in title for title in section_titles):
                return False
        
        return True 