"""
Tool Registry for managing agent tools.

The Tool Registry is responsible for registering and retrieving tools that agents can use.
"""

from typing import Dict, List, Optional, Type
from src.core.agent.agent_tool_interface import AgentToolInterface


class ToolRegistry:
    """
    Registry for agent tools.
    
    The Tool Registry maintains a collection of tools that agents can use to perform
    specific tasks. Tools are registered with the registry and can be retrieved by name.
    """
    
    def __init__(self):
        """Initialize the tool registry with an empty dictionary of tools."""
        self._tools: Dict[str, AgentToolInterface] = {}
    
    def register_tool(self, tool: AgentToolInterface) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: The tool to register.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[AgentToolInterface]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool to retrieve.
            
        Returns:
            The tool if found, None otherwise.
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[AgentToolInterface]:
        """
        List all registered tools.
        
        Returns:
            A list of all registered tools.
        """
        return list(self._tools.values())
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool by name.
        
        Args:
            name: The name of the tool to unregister.
            
        Returns:
            True if the tool was unregistered, False otherwise.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False 