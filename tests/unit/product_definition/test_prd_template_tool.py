"""
Unit tests for the PRD Template Tool.
"""

import pytest
import logging
from unittest.mock import patch

from src.product_definition.agents.tools.prd_template_tool import (
    PRDTemplateTool,
    PRDTemplateInput,
    PRDTemplateOutput
)


@pytest.fixture
def prd_template_tool():
    """Create a PRD Template Tool instance for testing."""
    return PRDTemplateTool()


def test_prd_template_tool_properties(prd_template_tool):
    """Test PRD Template Tool properties."""
    # Verify name and description
    assert prd_template_tool.name == "prd_template"
    assert "product requirement document" in prd_template_tool.description.lower()


def test_validate_input_valid(prd_template_tool):
    """Test input validation with valid input."""
    # Test with valid template types
    for template_type in ["basic", "detailed", "technical"]:
        input_data = PRDTemplateInput(template_type=template_type)
        result = prd_template_tool.validate_input(input_data)
        assert result is True


def test_validate_input_invalid(prd_template_tool):
    """Test input validation with invalid input."""
    # Test with invalid template type
    input_data = PRDTemplateInput(template_type="invalid_type")
    result = prd_template_tool.validate_input(input_data)
    assert result is False

    # Test with empty template type
    input_data = PRDTemplateInput(template_type="")
    result = prd_template_tool.validate_input(input_data)
    assert result is False


@pytest.mark.asyncio
async def test_execute_basic_template(prd_template_tool):
    """Test executing the tool with basic template type."""
    # Test with basic template type
    input_data = PRDTemplateInput(template_type="basic")
    result = await prd_template_tool.execute(input_data)
    
    # Verify result is a PRDTemplateOutput
    assert isinstance(result, PRDTemplateOutput)
    
    # Verify template content is not empty
    assert result.template_content is not None
    assert len(result.template_content) > 0
    
    # Verify sections are provided
    assert result.sections is not None
    assert len(result.sections) > 0
    
    # Verify basic sections are included
    basic_sections = ["Overview", "Problem Statement", "User Needs", "Solution", "Key Features", "Success Metrics"]
    for section in basic_sections:
        assert section in result.sections


@pytest.mark.asyncio
async def test_execute_detailed_template(prd_template_tool):
    """Test executing the tool with detailed template type."""
    # Test with detailed template type
    input_data = PRDTemplateInput(template_type="detailed")
    result = await prd_template_tool.execute(input_data)
    
    # Verify result is a PRDTemplateOutput
    assert isinstance(result, PRDTemplateOutput)
    
    # Verify template content is not empty
    assert result.template_content is not None
    assert len(result.template_content) > 0
    
    # Verify sections are provided
    assert result.sections is not None
    assert len(result.sections) > 0
    
    # Verify detailed sections are included
    detailed_sections = [
        "Executive Summary", "Problem Definition", "Objectives", "User Personas", 
        "User Journeys", "Functional Requirements", "Non-Functional Requirements", 
        "Metrics and Analytics", "Rollout Strategy", "Risks and Mitigations"
    ]
    for section in detailed_sections:
        assert section in result.sections


@pytest.mark.asyncio
async def test_execute_technical_template(prd_template_tool):
    """Test executing the tool with technical template type."""
    # Test with technical template type
    input_data = PRDTemplateInput(template_type="technical")
    result = await prd_template_tool.execute(input_data)
    
    # Verify result is a PRDTemplateOutput
    assert isinstance(result, PRDTemplateOutput)
    
    # Verify template content is not empty
    assert result.template_content is not None
    assert len(result.template_content) > 0
    
    # Verify sections are provided
    assert result.sections is not None
    assert len(result.sections) > 0
    
    # Verify technical sections are included
    technical_sections = [
        "System Overview", "Architecture", "Data Models", "API Specifications",
        "Integration Points", "Performance Requirements", "Security Requirements",
        "Testing Strategy", "Deployment Strategy", "Technical Risks"
    ]
    for section in technical_sections:
        assert section in result.sections


@pytest.mark.asyncio
async def test_execute_with_variables(prd_template_tool):
    """Test executing the tool with variables."""
    # Test with variables
    variables = {
        "product_name": "Test Product",
        "author": "Test Author",
        "date": "2023-01-01",
    }
    input_data = PRDTemplateInput(template_type="basic", variables=variables)
    result = await prd_template_tool.execute(input_data)
    
    # Verify variables are included in the template content
    assert "Test Product" in result.template_content
    assert "Test Author" in result.template_content
    assert "2023-01-01" in result.template_content


@pytest.mark.asyncio
async def test_handle_error(prd_template_tool, caplog):
    """Test error handling."""
    # Setup logging capture
    caplog.set_level(logging.ERROR)
    
    # Create a mock exception
    error = Exception("Test error")
    
    # Handle the error
    with patch.object(prd_template_tool, '_get_basic_template', side_effect=error):
        input_data = PRDTemplateInput(template_type="basic")
        result = await prd_template_tool.handle_error(input_data, error)
        
        # Verify error was logged
        assert "Error executing PRD Template Tool" in caplog.text
        assert "Test error" in caplog.text
        
        # Verify fallback template was returned
        assert isinstance(result, PRDTemplateOutput)
        assert "Fallback Product Requirement Document Template" in result.template_content
        assert len(result.sections) > 0 