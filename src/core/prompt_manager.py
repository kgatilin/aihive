"""
Prompt management for AI agents.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages prompts for all AI agents.
    
    Loads prompt templates from a YAML file and provides an interface to retrieve
    them by agent and function name.
    """
    
    def __init__(self, prompt_file_path: Optional[str] = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompt_file_path: Path to the YAML file containing prompts (optional)
                If not provided, the default path is used (config/prompts.yaml)
        """
        self._prompts = {}
        self._prompt_file_path = prompt_file_path or os.path.join("config", "prompts.yaml")
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from the YAML file."""
        try:
            with open(self._prompt_file_path, 'r') as file:
                self._prompts = yaml.safe_load(file) or {}
                logger.info(f"Loaded prompts from {self._prompt_file_path}")
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {self._prompt_file_path}")
            self._prompts = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing prompt file: {e}")
            self._prompts = {}
    
    def get_prompt(self, agent_name: str, prompt_name: str, fallback: Optional[str] = None) -> str:
        """
        Get a prompt template for an agent and prompt name.
        
        Args:
            agent_name: The name of the agent (e.g., 'product_manager_agent')
            prompt_name: The name of the prompt (e.g., 'analyze_user_request')
            fallback: Optional fallback prompt if the requested prompt is not found
        
        Returns:
            The prompt template string
        
        Raises:
            KeyError: If the prompt is not found and no fallback is provided
        """
        try:
            return self._prompts.get(agent_name, {}).get(prompt_name, fallback)
        except (AttributeError, KeyError):
            if fallback is not None:
                return fallback
            raise KeyError(f"Prompt '{prompt_name}' not found for agent '{agent_name}'")
    
    def format_prompt(self, agent_name: str, prompt_name: str, 
                     template_vars: Dict[str, Any] = None, 
                     fallback: Optional[str] = None) -> str:
        """
        Get and format a prompt with template variables.
        
        Args:
            agent_name: The name of the agent
            prompt_name: The name of the prompt
            template_vars: Dictionary of variables to substitute in the template
            fallback: Optional fallback prompt if the requested prompt is not found
        
        Returns:
            The formatted prompt string
        """
        template = self.get_prompt(agent_name, prompt_name, fallback)
        if template and template_vars:
            try:
                return template.format(**template_vars)
            except KeyError as e:
                logger.warning(f"Missing template variable in prompt: {e}")
                # Return the unformatted template if formatting fails
                return template
        return template

    def reload_prompts(self):
        """Reload prompts from the YAML file."""
        self._load_prompts()


# Global prompt manager instance
_prompt_manager_instance = None

def get_prompt_manager() -> PromptManager:
    """
    Get the global prompt manager instance.
    
    Returns:
        The prompt manager instance
    """
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance 