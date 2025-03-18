"""
Tests for the PromptManager class.
"""

import os
import tempfile
import pytest
import yaml
from src.core.prompt_manager import PromptManager


@pytest.fixture
def temp_prompt_file():
    """Create a temporary prompt YAML file for testing."""
    content = {
        "test_agent": {
            "base_prompt": "This is a test prompt for {agent_name}",
            "special_prompt": "This is a special prompt with {variable}"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        yaml.dump(content, tmp)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up the temp file
    os.unlink(tmp_path)


def test_load_prompts(temp_prompt_file):
    """Test loading prompts from a YAML file."""
    manager = PromptManager(temp_prompt_file)
    
    # Check that prompts were loaded
    prompt = manager.get_prompt("test_agent", "base_prompt")
    assert prompt == "This is a test prompt for {agent_name}"
    
    # Check that we can get a specific prompt
    prompt = manager.get_prompt("test_agent", "special_prompt")
    assert prompt == "This is a special prompt with {variable}"


def test_format_prompt(temp_prompt_file):
    """Test formatting a prompt with variables."""
    manager = PromptManager(temp_prompt_file)
    
    # Format a prompt with variables
    formatted = manager.format_prompt(
        "test_agent", 
        "base_prompt", 
        {"agent_name": "TestBot"}
    )
    
    assert formatted == "This is a test prompt for TestBot"


def test_fallback_prompt(temp_prompt_file):
    """Test fallback to default prompt when requested prompt is not found."""
    manager = PromptManager(temp_prompt_file)
    
    # Try to get a non-existent prompt with a fallback
    prompt = manager.get_prompt(
        "test_agent", 
        "non_existent_prompt", 
        fallback="Fallback prompt"
    )
    
    assert prompt == "Fallback prompt"


def test_missing_prompt():
    """Test behavior when prompt file is missing."""
    # Use a non-existent file path
    manager = PromptManager("non_existent_file.yaml")
    
    # Should return None for a non-existent prompt
    prompt = manager.get_prompt("test_agent", "base_prompt")
    assert prompt is None
    
    # Should use fallback if provided
    prompt = manager.get_prompt("test_agent", "base_prompt", fallback="Default")
    assert prompt == "Default"


def test_reload_prompts(temp_prompt_file):
    """Test reloading prompts after file changes."""
    manager = PromptManager(temp_prompt_file)
    
    # Get initial prompt
    initial_prompt = manager.get_prompt("test_agent", "base_prompt")
    assert initial_prompt == "This is a test prompt for {agent_name}"
    
    # Modify the file
    new_content = {
        "test_agent": {
            "base_prompt": "This is an updated prompt for {agent_name}",
            "special_prompt": "This is a special prompt with {variable}"
        }
    }
    
    with open(temp_prompt_file, 'w') as f:
        yaml.dump(new_content, f)
    
    # Reload prompts
    manager.reload_prompts()
    
    # Get updated prompt
    updated_prompt = manager.get_prompt("test_agent", "base_prompt")
    assert updated_prompt == "This is an updated prompt for {agent_name}" 