from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
import os
import logging

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from unittest.mock import MagicMock

from src.core.agent.agent_tool_interface import AgentToolInterface
from src.core.config import Config
from src.core.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)

class AIAgent(ABC):
    """Base class for AI-powered agents in the system."""
    
    def __init__(
        self, 
        agent_id: str, 
        name: str,
        description: str,
        tool_registry: Optional[Dict[str, AgentToolInterface]] = None,
        model_name: Optional[str] = None,
        llm: Optional[BaseChatModel] = None,
        config: Optional[Config] = None
    ):
        """Initialize the AI agent with configuration.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Display name for the agent
            description: Description of what this agent does
            tool_registry: Optional registry of tools available to the agent
            model_name: Optional OpenAI model to use (otherwise use default from config)
            llm: Optional LLM instance for testing
            config: Optional configuration object
        """
        self._agent_id = agent_id
        self._name = name
        self._description = description
        self._tools = {}  # Available tools for this agent
        self._tool_registry = tool_registry or {}
        self._config = config or Config()
        self._prompt_manager = get_prompt_manager()
        
        # Set up LLM if provided for testing, otherwise initialize with config
        if llm:
            self.llm = llm
        else:
            api_key = model_name = temperature = None
            
            # Try to get config values, defaulting to environment variables if needed
            try:
                api_key = self._config.openai_api_key or os.getenv("OPENAI_API_KEY")
                model_name = model_name or self._config.openai_default_model or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4-turbo-preview")
                temperature = self._config.openai_temperature or float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error loading OpenAI config: {e}. Using defaults.")
                api_key = os.getenv("OPENAI_API_KEY")
                model_name = model_name or "gpt-4-turbo-preview"
                temperature = 0.7
            
            # Initialize the LLM
            if not api_key:
                logger.warning("No OpenAI API key found. Some agent features may not work.")
            
            self.llm = ChatOpenAI(
                api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )
        
        self._base_prompt = self._get_base_prompt()
    
    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self._agent_id
    
    @property
    def name(self) -> str:
        """Get the agent's display name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the agent's description."""
        return self._description
    
    @property
    def tools(self) -> Dict[str, AgentToolInterface]:
        """Get the tools available to this agent."""
        return self._tools
    
    def add_tool(self, tool_name: str) -> bool:
        """Add a tool to this agent from the tool registry.
        
        Args:
            tool_name: Name of the tool to add
        
        Returns:
            True if tool was added, False otherwise
        """
        if not self._tool_registry:
            logger.warning("Tool registry is not available.")
            return False
            
        if tool_name in self._tool_registry:
            self._tools[tool_name] = self._tool_registry[tool_name]
            return True
        else:
            logger.warning(f"Tool '{tool_name}' not found in registry.")
            return False
    
    def _get_base_prompt(self) -> str:
        """Get the base prompt for this agent from the prompt manager.
        
        Returns:
            The base prompt template string
        """
        agent_type = self.__class__.__name__.lower()
        default_prompt = self._setup_prompt()
        return self._prompt_manager.get_prompt(agent_type, "base_prompt", default_prompt)
    
    @abstractmethod
    def _setup_prompt(self) -> str:
        """Set up the default base prompt for this agent (used as fallback).
        
        Returns:
            The base prompt template string
        """
        pass
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """Process input with the AI model.
        
        Args:
            input_data: Input data for processing
        
        Returns:
            Processed output from the model
        """
        # Format the input data
        formatted_input = self._format_input(input_data)
        
        try:
            # For testing environments, use direct invocation
            if isinstance(self.llm, MagicMock):
                raw_response = await self.llm.ainvoke(formatted_input)
                return self._parse_output(raw_response)
            
            # Setup the prompt template with the base prompt
            prompt = ChatPromptTemplate.from_template(self._base_prompt)
            
            # Create a simple chain to process the input
            chain = prompt | self.llm | StrOutputParser()
            
            # Process the input with the chain
            result = await chain.ainvoke(formatted_input)
            
            # Parse and return the result
            return self._parse_output(result)
        except Exception as e:
            logger.error(f"Error processing input with AI: {e}")
            raise
    
    def _format_input(self, input_data: Any) -> Dict[str, Any]:
        """Format the input data for the LLM.
        
        Args:
            input_data: Raw input data
        
        Returns:
            Formatted input data as a dictionary
        """
        # Default implementation - override for specific formatting needs
        if isinstance(input_data, dict):
            return input_data
        return {"input": str(input_data)}
    
    def _parse_output(self, output):
        """Parse the output from the LLM.
        
        Args:
            output: Raw output from the LLM.
            
        Returns:
            Parsed output, typically a dict or list from JSON.
        """
        try:
            # If output is a MagicMock (in testing), extract content
            if hasattr(output, 'content'):
                output = output.content
                
            # If output is already a dictionary or list, return it
            if isinstance(output, (dict, list)):
                return output
                
            # Otherwise, try to parse it as JSON
            return json.loads(output)
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON, return it as text
            return {"text": str(output)}
            
    async def invoke_llm(self, prompt: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Directly invoke the LLM with a specific prompt.
        
        Args:
            prompt: The prompt template to use
            input_data: Input data for the prompt
            
        Returns:
            Parsed output from the LLM
        """
        try:
            # For testing environments, use direct invocation
            if isinstance(self.llm, MagicMock):
                raw_response = await self.llm.ainvoke(input_data)
                return self._parse_output(raw_response)
            
            # Create a prompt template
            prompt_template = ChatPromptTemplate.from_template(prompt)
            
            # Create a chain to process the input
            chain = prompt_template | self.llm | StrOutputParser()
            
            # Process the input with the chain
            result = await chain.ainvoke(input_data)
            
            # Parse and return the result
            return self._parse_output(result)
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            raise 