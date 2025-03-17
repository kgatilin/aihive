"""
This module defines the interface for Agent Tools used by AI agents to interact with the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic

# Generic type for tool input and output
T_Input = TypeVar('T_Input')
T_Output = TypeVar('T_Output')


class AgentToolInterface(Generic[T_Input, T_Output], ABC):
    """
    Interface defining the contract for agent tools.
    Agent tools provide a structured way for agents to interact with the system,
    ensuring proper authorization and validation.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            The name of the tool
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the tool.
        
        Returns:
            The description of the tool
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: T_Input) -> bool:
        """
        Validate the input data before executing the tool.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: T_Input) -> T_Output:
        """
        Execute the tool with the given input data.
        
        Args:
            input_data: The input data for the tool
            
        Returns:
            The output of the tool execution
        """
        pass
    
    @abstractmethod
    async def handle_error(self, error: Exception, input_data: T_Input) -> Optional[T_Output]:
        """
        Handle errors that occur during tool execution.
        
        Args:
            error: The exception that occurred
            input_data: The input data that caused the error
            
        Returns:
            Optional fallback output or None
        """
        pass


class ToolRegistry:
    """
    Registry for agent tools, allowing agents to discover and use available tools.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, AgentToolInterface] = {}
    
    def register_tool(self, tool: AgentToolInterface) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: The tool to register
        """
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[AgentToolInterface]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """
        List all available tools with their descriptions.
        
        Returns:
            A list of dictionaries containing tool information
        """
        return [{"name": tool.name, "description": tool.description} for tool in self._tools.values()] 