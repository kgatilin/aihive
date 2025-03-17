"""
PRD Template Tool for generating product requirement document templates.

This tool provides templates for product requirement documents based on the level of detail
needed: basic, detailed, or technical.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.core.agent.agent_tool_interface import AgentToolInterface


logger = logging.getLogger(__name__)


@dataclass
class PRDTemplateInput:
    """Input for the PRD Template Tool."""
    template_type: str  # "basic", "detailed", or "technical"
    variables: Optional[Dict[str, str]] = None


@dataclass
class PRDTemplateOutput:
    """Output of the PRD Template Tool."""
    template_content: str
    sections: List[str]


class PRDTemplateTool(AgentToolInterface):
    """
    Tool for generating product requirement document templates.
    
    This tool provides templates for product requirement documents based on the level of detail
    needed: basic, detailed, or technical.
    """
    
    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return "prd_template"
    
    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return (
            "Generates a Product Requirement Document (PRD) template based on the specified "
            "level of detail (basic, detailed, or technical)."
        )
    
    def validate_input(self, input_data: PRDTemplateInput) -> bool:
        """
        Validate the input data for the tool.
        
        Args:
            input_data: The input data for the tool.
            
        Returns:
            True if the input is valid, False otherwise.
        """
        valid_template_types = ["basic", "detailed", "technical"]
        
        if not input_data.template_type:
            logger.warning("Template type is empty")
            return False
        
        if input_data.template_type not in valid_template_types:
            logger.warning(f"Invalid template type: {input_data.template_type}")
            return False
        
        return True
    
    async def execute(self, input_data: PRDTemplateInput) -> PRDTemplateOutput:
        """
        Generate a PRD template based on the specified template type.
        
        Args:
            input_data: The input data for the tool.
            
        Returns:
            The generated PRD template.
        """
        logger.info(f"Generating {input_data.template_type} PRD template")
        
        if input_data.template_type == "basic":
            return await self._get_basic_template(input_data.variables or {})
        elif input_data.template_type == "detailed":
            return await self._get_detailed_template(input_data.variables or {})
        elif input_data.template_type == "technical":
            return await self._get_technical_template(input_data.variables or {})
        else:
            # This shouldn't happen if validate_input is called before execute
            raise ValueError(f"Invalid template type: {input_data.template_type}")
    
    async def handle_error(self, input_data: PRDTemplateInput, error: Exception) -> PRDTemplateOutput:
        """
        Handle errors during tool execution.
        
        Args:
            input_data: The input data for the tool.
            error: The error that occurred.
            
        Returns:
            A fallback template.
        """
        logger.error(f"Error executing PRD Template Tool: {str(error)}")
        
        # Provide a minimal fallback template
        fallback_template = """# Fallback Product Requirement Document Template

## Overview
[Provide a brief overview of the product or feature]

## Problem Statement
[Describe the problem this product or feature aims to solve]

## User Needs
[Describe the user needs this product or feature addresses]

## Solution
[Describe the proposed solution]

## Key Features
[List the key features of the product or feature]

## Success Metrics
[Define how success will be measured]
"""
        
        return PRDTemplateOutput(
            template_content=fallback_template,
            sections=["Overview", "Problem Statement", "User Needs", "Solution", "Key Features", "Success Metrics"]
        )
    
    async def _get_basic_template(self, variables: Dict[str, str]) -> PRDTemplateOutput:
        """
        Generate a basic PRD template.
        
        Args:
            variables: The variables to replace in the template.
            
        Returns:
            The generated PRD template.
        """
        # Apply variables to the template
        product_name = variables.get("product_name", "[Product Name]")
        author = variables.get("author", "[Author]")
        date = variables.get("date", "[Date]")
        
        template_content = f"""# Product Requirement Document: {product_name}
Author: {author}
Date: {date}

## Overview
[Provide a brief overview of the product or feature. What is it and why is it needed?]

## Problem Statement
[Describe the problem this product or feature aims to solve. What challenges do users face?]

## User Needs
[Describe the user needs this product or feature addresses. Who are the users and what do they need?]

## Solution
[Describe the proposed solution. How will this product or feature solve the problem?]

## Key Features
[List the key features of the product or feature. What will it do?]
- Feature 1: [Description]
- Feature 2: [Description]
- Feature 3: [Description]

## Success Metrics
[Define how success will be measured. What goals should this product or feature achieve?]
- Metric 1: [Description]
- Metric 2: [Description]
"""
        
        sections = ["Overview", "Problem Statement", "User Needs", "Solution", "Key Features", "Success Metrics"]
        
        return PRDTemplateOutput(template_content=template_content, sections=sections)
    
    async def _get_detailed_template(self, variables: Dict[str, str]) -> PRDTemplateOutput:
        """
        Generate a detailed PRD template.
        
        Args:
            variables: The variables to replace in the template.
            
        Returns:
            The generated PRD template.
        """
        # Apply variables to the template
        product_name = variables.get("product_name", "[Product Name]")
        author = variables.get("author", "[Author]")
        date = variables.get("date", "[Date]")
        
        template_content = f"""# Detailed Product Requirement Document: {product_name}
Author: {author}
Date: {date}
Version: 1.0

## Executive Summary
[Provide a concise summary of the product or feature. Summarize the problem, solution, and key benefits.]

## Problem Definition
[Describe the problem in detail. Include data on the impact of the problem and how it affects users and business goals.]

## Objectives
[Define the specific objectives for this product or feature. What should it achieve?]
- Primary Objective: [Description]
- Secondary Objectives:
  - [Objective 1]
  - [Objective 2]

## User Personas
[Describe the primary user personas who will use this product or feature.]
### Persona 1: [Name]
- Background: [Description]
- Goals: [Description]
- Pain Points: [Description]
- Expectations: [Description]

### Persona 2: [Name]
- Background: [Description]
- Goals: [Description]
- Pain Points: [Description]
- Expectations: [Description]

## User Journeys
[Describe the key user journeys for this product or feature.]
### Journey 1: [Name]
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Journey 2: [Name]
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Functional Requirements
[List the functional requirements of the product or feature.]
### Requirement Category 1: [Name]
- FR1.1: [Description]
- FR1.2: [Description]

### Requirement Category 2: [Name]
- FR2.1: [Description]
- FR2.2: [Description]

## Non-Functional Requirements
[List the non-functional requirements of the product or feature.]
- Performance: [Description]
- Scalability: [Description]
- Security: [Description]
- Usability: [Description]
- Reliability: [Description]

## Metrics and Analytics
[Define how success will be measured. What data points will be tracked?]
- Key Performance Indicators:
  - KPI 1: [Description]
  - KPI 2: [Description]
- User Analytics:
  - Metric 1: [Description]
  - Metric 2: [Description]

## Rollout Strategy
[Describe how the product or feature will be rolled out.]
- Phase 1: [Description]
- Phase 2: [Description]
- Phase 3: [Description]

## Risks and Mitigations
[Identify potential risks and how they will be mitigated.]
- Risk 1: [Description]
  - Mitigation: [Description]
- Risk 2: [Description]
  - Mitigation: [Description]
"""
        
        sections = [
            "Executive Summary", "Problem Definition", "Objectives", "User Personas", 
            "User Journeys", "Functional Requirements", "Non-Functional Requirements", 
            "Metrics and Analytics", "Rollout Strategy", "Risks and Mitigations"
        ]
        
        return PRDTemplateOutput(template_content=template_content, sections=sections)
    
    async def _get_technical_template(self, variables: Dict[str, str]) -> PRDTemplateOutput:
        """
        Generate a technical PRD template.
        
        Args:
            variables: The variables to replace in the template.
            
        Returns:
            The generated PRD template.
        """
        # Apply variables to the template
        product_name = variables.get("product_name", "[Product Name]")
        author = variables.get("author", "[Author]")
        date = variables.get("date", "[Date]")
        
        template_content = f"""# Technical Product Requirement Document: {product_name}
Author: {author}
Date: {date}
Version: 1.0

## System Overview
[Provide a technical overview of the system or feature. What is it and how does it fit into the existing architecture?]

## Architecture
[Describe the architecture of the system or feature. Include diagrams and component descriptions.]
### System Components
- Component 1: [Description]
- Component 2: [Description]
- Component 3: [Description]

### Architecture Diagram
[Insert architecture diagram here]

## Data Models
[Describe the data models used by the system or feature.]
### Model 1: [Name]
- Field 1: [Type, Description]
- Field 2: [Type, Description]
- Field 3: [Type, Description]

### Model 2: [Name]
- Field 1: [Type, Description]
- Field 2: [Type, Description]
- Field 3: [Type, Description]

## API Specifications
[Describe the APIs provided by the system or feature.]
### Endpoint 1: [Method] [Path]
- Description: [Description]
- Request Parameters:
  - Parameter 1: [Type, Description]
  - Parameter 2: [Type, Description]
- Response:
  - Status Code: [Code, Description]
  - Response Body: [Description]

### Endpoint 2: [Method] [Path]
- Description: [Description]
- Request Parameters:
  - Parameter 1: [Type, Description]
  - Parameter 2: [Type, Description]
- Response:
  - Status Code: [Code, Description]
  - Response Body: [Description]

## Integration Points
[Describe how the system or feature integrates with other systems.]
### Integration 1: [Name]
- Description: [Description]
- Integration Type: [Type]
- Data Flow: [Description]

### Integration 2: [Name]
- Description: [Description]
- Integration Type: [Type]
- Data Flow: [Description]

## Performance Requirements
[Describe the performance requirements for the system or feature.]
- Latency: [Description]
- Throughput: [Description]
- Resource Usage: [Description]

## Security Requirements
[Describe the security requirements for the system or feature.]
- Authentication: [Description]
- Authorization: [Description]
- Data Protection: [Description]
- Compliance: [Description]

## Testing Strategy
[Describe how the system or feature will be tested.]
- Unit Testing: [Description]
- Integration Testing: [Description]
- Performance Testing: [Description]
- Security Testing: [Description]

## Deployment Strategy
[Describe how the system or feature will be deployed.]
- Environments: [Description]
- Deployment Process: [Description]
- Rollback Plan: [Description]

## Technical Risks
[Identify potential technical risks and how they will be mitigated.]
- Risk 1: [Description]
  - Mitigation: [Description]
- Risk 2: [Description]
  - Mitigation: [Description]
"""
        
        sections = [
            "System Overview", "Architecture", "Data Models", "API Specifications",
            "Integration Points", "Performance Requirements", "Security Requirements",
            "Testing Strategy", "Deployment Strategy", "Technical Risks"
        ]
        
        return PRDTemplateOutput(template_content=template_content, sections=sections) 