"""
Orchestrator Agent implementation.

This agent is responsible for coordinating multiple AI agents, distributing tasks,
and managing the workflow between agents.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from src.core.agent.ai_agent import AIAgent
from src.task_management.domain.entities.task import Task
from src.task_management.application.task_service import TaskService
from src.task_management.domain.value_objects.task_status import TaskStatus


logger = logging.getLogger(__name__)


class OrchestratorAgent(AIAgent):
    """
    Orchestrator Agent implementation.
    
    This agent coordinates multiple AI agents, distributes tasks, and manages
    the workflow between different agents.
    """
    
    def __init__(
        self,
        task_service: TaskService,
        agents: Dict[str, AIAgent] = None,
        agent_id: str = "orchestrator-agent",
        model_name: str = "gpt-4-turbo-preview"
    ):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            task_service: The task service for interacting with tasks.
            agents: Dictionary of agents managed by the orchestrator.
            agent_id: The ID of the agent.
            model_name: The name of the OpenAI model to use.
        """
        # Initialize AIAgent first
        super().__init__(model_name=model_name)
        
        self._task_service = task_service
        self._agents = agents or {}
        self._agent_id = agent_id
    
    def _setup_prompt(self) -> None:
        """Set up the system prompt for the agent."""
        self.system_prompt = """
        You are an Orchestrator Agent responsible for:
        1. Analyzing incoming tasks and determining which agent should handle them
        2. Coordinating workflows between multiple specialized AI agents
        3. Managing dependencies between tasks
        4. Ensuring all tasks are completed efficiently
        
        You should evaluate tasks based on:
        - The nature and requirements of the task
        - The specializations of available agents
        - Current workload of each agent
        - Dependencies between tasks
        
        When making decisions, focus on:
        - Optimizing for efficiency
        - Ensuring appropriate agent assignment
        - Maintaining a coherent workflow
        - Handling dependencies correctly
        
        Available agents:
        {agents}
        
        Available tools:
        {tools}
        """
        
        # Create agent descriptions
        agent_descriptions = "\n".join(
            f"- {agent_id}: {agent.__class__.__name__}"
            for agent_id, agent in self._agents.items()
        )
        
        # Add agent and tool descriptions to the prompt
        self.system_prompt = self.system_prompt.format(
            agents=agent_descriptions,
            tools=self._get_tool_descriptions()
        )
    
    @property
    def agent_id(self) -> str:
        """Get the agent's identifier."""
        return self._agent_id
    
    def add_agent(self, agent_id: str, agent: AIAgent) -> None:
        """
        Add an agent to the orchestrator.
        
        Args:
            agent_id: The ID of the agent.
            agent: The agent instance.
        """
        self._agents[agent_id] = agent
        # Update the system prompt to include the new agent
        self._setup_prompt()
    
    async def process_task(self, task: Task) -> Task:
        """
        Process a task by determining which agent should handle it.
        
        Args:
            task: The task to process.
            
        Returns:
            The processed task with updated status.
        """
        logger.info(f"Orchestrator processing task {task.task_id}: {task.title}")
        
        try:
            # Update task status to in progress
            task = await self._task_service.update_task_status(
                task_id=task.task_id,
                new_status=TaskStatus.IN_PROGRESS.value,
                changed_by=self.agent_id,
                reason="Starting to analyze task for agent assignment"
            )
            
            # Determine which agent should handle this task
            assigned_agent_id = await self.determine_agent_for_task(task)
            
            if assigned_agent_id and assigned_agent_id in self._agents:
                logger.info(f"Assigning task {task.task_id} to agent {assigned_agent_id}")
                
                # Update task with assignment info
                await self._task_service.add_comment(
                    task_id=task.task_id,
                    comment=f"This task has been assigned to {assigned_agent_id}",
                    created_by=self.agent_id
                )
                
                # Assign the task to the selected agent
                assigned_agent = self._agents[assigned_agent_id]
                task = await assigned_agent.process_task(task)
                
                return task
            else:
                logger.error(f"Could not find appropriate agent for task {task.task_id}")
                
                # Update task status to blocked
                task = await self._task_service.update_task_status(
                    task_id=task.task_id,
                    new_status=TaskStatus.BLOCKED.value,
                    changed_by=self.agent_id,
                    reason="Could not find appropriate agent to handle this task"
                )
                
                await self._task_service.add_comment(
                    task_id=task.task_id,
                    comment="No suitable agent found to process this task. Manual assignment needed.",
                    created_by=self.agent_id
                )
                
                return task
        except Exception as e:
            logger.error(f"Error in orchestrator processing task {task.task_id}: {str(e)}")
            
            # Update task status to failed
            task = await self._task_service.update_task_status(
                task_id=task.task_id,
                new_status=TaskStatus.CANCELED.value,
                changed_by=self.agent_id,
                reason=f"Error processing task: {str(e)}"
            )
            
            return task
    
    async def determine_agent_for_task(self, task: Task) -> Optional[str]:
        """
        Determine which agent should handle a specific task using LLM.
        
        Args:
            task: The task to analyze.
            
        Returns:
            The ID of the agent that should handle the task, or None if no agent is suitable.
        """
        # If we have only one agent, assign to that agent
        if len(self._agents) == 1:
            return next(iter(self._agents.keys()))
        
        # Prepare input for the LLM
        agent_descriptions = "\n".join(
            f"- {agent_id}: {agent.__class__.__name__}"
            for agent_id, agent in self._agents.items()
        )
        
        prompt = f"""
        Analyze the following task and determine which agent should handle it.
        
        Task Title: {task.title}
        Task Description: {task.description}
        Task Priority: {task.priority.value if hasattr(task, 'priority') else 'Unknown'}
        
        Available agents:
        {agent_descriptions}
        
        Return your decision as a JSON object with the following fields:
        - agent_id: The ID of the agent that should handle this task
        - reason: A brief explanation of why this agent is the best choice
        
        JSON Format:
        ```json
        {{
          "agent_id": string,
          "reason": string
        }}
        ```
        Only return the JSON object, nothing else.
        """
        
        # Call the LLM
        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ])
        
        try:
            # Extract the JSON from the response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            assignment = json.loads(content.strip())
            
            # Log the assignment decision
            logger.info(f"Agent assignment decision: {assignment}")
            
            # Add a comment to the task with the assignment reason
            await self._task_service.add_comment(
                task_id=task.task_id,
                comment=f"Task assigned to {assignment['agent_id']}: {assignment['reason']}",
                created_by=self.agent_id
            )
            
            return assignment["agent_id"]
        except Exception as e:
            logger.error(f"Error determining agent for task: {str(e)}")
            return None
    
    async def handle_agent_failure(self, task: Task, failed_agent_id: str) -> Task:
        """
        Handle a task that an agent failed to process.
        
        Args:
            task: The failed task.
            failed_agent_id: The ID of the agent that failed.
            
        Returns:
            The task with updated status.
        """
        logger.info(f"Handling failure of agent {failed_agent_id} for task {task.task_id}")
        
        # Update task status to blocked
        task = await self._task_service.update_task_status(
            task_id=task.task_id,
            new_status=TaskStatus.BLOCKED.value,
            changed_by=self.agent_id,
            reason=f"Agent {failed_agent_id} failed to process this task"
        )
        
        # Analyze the failure using LLM
        prompt = f"""
        Analyze the following task that failed processing by agent {failed_agent_id}.
        Determine if another agent could handle it or if manual intervention is needed.
        
        Task Title: {task.title}
        Task Description: {task.description}
        Failed Agent: {failed_agent_id}
        
        Return your analysis as a JSON object with the following fields:
        - reassign: (true/false) whether to reassign the task to another agent
        - new_agent_id: (if reassign is true) the ID of the agent to reassign to
        - reason: A brief explanation of your decision
        
        JSON Format:
        ```json
        {{
          "reassign": boolean,
          "new_agent_id": string,
          "reason": string
        }}
        ```
        Only return the JSON object, nothing else.
        """
        
        # Call the LLM
        response = await self.llm.ainvoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ])
        
        try:
            # Extract the JSON from the response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            analysis = json.loads(content.strip())
            
            # Log the analysis
            logger.info(f"Failure analysis: {analysis}")
            
            if analysis.get("reassign", False) and analysis.get("new_agent_id") in self._agents:
                # Add a comment about reassignment
                await self._task_service.add_comment(
                    task_id=task.task_id,
                    comment=f"Task reassigned from {failed_agent_id} to {analysis['new_agent_id']}: {analysis['reason']}",
                    created_by=self.agent_id
                )
                
                # Reassign to the new agent
                new_agent = self._agents[analysis["new_agent_id"]]
                task = await new_agent.process_task(task)
                return task
            else:
                # Add a comment about manual intervention
                await self._task_service.add_comment(
                    task_id=task.task_id,
                    comment=f"Task requires manual intervention after failure by {failed_agent_id}: {analysis.get('reason', 'No specific reason provided')}",
                    created_by=self.agent_id
                )
                return task
        except Exception as e:
            logger.error(f"Error analyzing agent failure: {str(e)}")
            
            # Add a generic comment
            await self._task_service.add_comment(
                task_id=task.task_id,
                comment=f"Task failed processing by {failed_agent_id} and requires manual review.",
                created_by=self.agent_id
            )
            return task 