import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.core.agent.agent_tool_interface import AgentToolInterface
from src.core.config import Config
from src.task_management.models.task import Task, TaskStatus, TaskPriority
from src.product_definition.agents.product_manager_agent import ProductManagerAgent
from src.product_definition.models.product_requirement import ProductRequirement as PRD
from src.product_definition.domain.interfaces.product_requirement_repository_interface import ProductRequirementRepositoryInterface
from src.task_management.services.task_service import TaskService


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_id="task123",
        title="Create Login Feature",
        description="Implement a user login feature with email and password authentication",
        created_by="user123",
        status=TaskStatus.CREATED.value,
        priority=TaskPriority.MEDIUM,
        tags=["type:feature", "component:auth"]
    )


@pytest.fixture
def mock_task_service():
    """Mock the TaskService."""
    mock = MagicMock(spec=TaskService)
    
    # Setup common method returns
    mock.update_task_status.return_value = MagicMock(spec=Task)
    mock.add_comment.return_value = None
    
    return mock


@pytest.fixture
def mock_product_requirement_repository():
    """Mock the ProductRequirementRepository."""
    mock = MagicMock(spec=ProductRequirementRepositoryInterface)
    
    # Setup the create method to return the input
    mock.create.side_effect = lambda x: x
    
    return mock


@pytest.fixture
def mock_tool_registry():
    """Mock the ToolRegistry."""
    return {}


@pytest.fixture
def mock_chat_openai():
    """Mock the ChatOpenAI class."""
    mock = MagicMock()
    
    # Create a custom ainvoke method
    async def mock_ainvoke(*args, **kwargs):
        return json.dumps({
            "clarity_score": 7.0,
            "completeness_score": 6.0,
            "key_features": ["User login with email/password", "Authentication"],
            "target_audience": "End users",
            "product_type": "Web application",
            "missing_information": ["Security requirements", "User flow details"]
        })
        
    mock.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    return mock


@pytest.fixture
def mock_config():
    """Create a mock Config."""
    mock = MagicMock(spec=Config)
    mock.openai_api_key = "mock-api-key"
    mock.openai_default_model = "gpt-4-test"
    mock.openai_temperature = 0.5
    return mock


@pytest.fixture
def product_manager_agent(mock_task_service, mock_product_requirement_repository, mock_tool_registry, mock_chat_openai, mock_config):
    """Create a ProductManagerAgent instance."""
    agent = ProductManagerAgent(
        task_service=mock_task_service,
        product_requirement_repository=mock_product_requirement_repository,
        tool_registry=mock_tool_registry,
        llm=mock_chat_openai,
        config=mock_config
    )
    
    return agent


class TestAIProductManagerAgent:
    """Tests for the AI-powered Product Manager Agent."""
    
    @pytest.mark.asyncio
    async def test_analyze_user_request(self, product_manager_agent, sample_task, mock_chat_openai):
        """Test analyzing a user request with LLM."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return json.dumps({
                "clarity_score": 7.0,
                "completeness_score": 6.0,
                "key_features": ["User login with email/password", "Authentication"],
                "target_audience": "End users",
                "product_type": "Web application",
                "missing_information": ["Security requirements", "User flow details"]
            })
        
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Call the method
        analysis = await product_manager_agent.analyze_user_request(sample_task)
        
        # Verify the result
        assert analysis["clarity_score"] == 7.0
        assert analysis["completeness_score"] == 6.0
        assert "Security requirements" in analysis["missing_information"]
        assert "User flow details" in analysis["missing_information"]
        
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self, product_manager_agent, sample_task, mock_chat_openai):
        """Test generating clarification questions with LLM."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return json.dumps([
                "What security requirements should be implemented for the login feature?",
                "Could you describe the user flow for authentication in more detail?",
                "Are there any specific password requirements or constraints?"
            ])
            
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Create a test analysis
        analysis = {
            "clarity_score": 4.5,
            "completeness_score": 5.0,
            "key_features": ["User login"],
            "target_audience": "unknown",
            "product_type": "Web application",
            "missing_information": ["target_audience", "success_metrics"]
        }
        
        # Call the method
        questions = await product_manager_agent.generate_clarification_questions(sample_task, analysis)
        
        # Verify the result
        assert len(questions) == 3
        assert "security requirements" in questions[0].lower()
        assert "user flow" in questions[1].lower()
        assert "password requirements" in questions[2].lower()
            
    @pytest.mark.asyncio
    async def test_fallback_questions_generation(self, product_manager_agent, sample_task, mock_chat_openai):
        """Test fallback question generation when LLM fails."""
        # Set up the mock to raise an exception
        mock_chat_openai.ainvoke.side_effect = Exception("LLM error")
        
        # Create a test analysis
        analysis = {
            "clarity_score": 4.0,
            "completeness_score": 4.0,
            "key_features": [],
            "target_audience": "unknown",
            "product_type": "unknown",
            "missing_information": ["target_audience", "key_features", "product_type"]
        }
        
        # Call the method
        questions = await product_manager_agent.generate_clarification_questions(sample_task, analysis)
        
        # Verify fallback questions were generated
        assert len(questions) > 0
        assert any("target_audience" in q.lower() for q in questions)
        
    @pytest.mark.asyncio
    async def test_create_product_requirement_document(self, product_manager_agent, sample_task, mock_chat_openai):
        """Test creating a PRD with LLM."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return """# Login Feature PRD

## Overview
This document outlines the requirements for implementing a user login feature.

## Key Features
- User login with email and password
- Secure authentication

## User Needs
Users need a secure way to access their accounts.

## Success Metrics
- Successful login rate > 99%
"""
            
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Create a test analysis
        analysis = {
            "clarity_score": 8.0,
            "completeness_score": 7.0,
            "key_features": ["User login with email/password", "Authentication"],
            "target_audience": "End users",
            "product_type": "Web application",
            "missing_information": []
        }
        
        # Call the method
        prd = await product_manager_agent.create_product_requirement_document(sample_task, analysis)
        
        # Verify the result
        assert hasattr(prd, 'product_requirement_id')
        assert hasattr(prd, 'title')
        assert hasattr(prd, 'content')
        assert prd.title.startswith("Create Login Feature")
        assert "Login Feature PRD" in prd.content
        assert prd.related_task_id == sample_task.task_id
            
    @pytest.mark.asyncio
    async def test_validate_product_requirement_document(self, product_manager_agent, mock_chat_openai):
        """Test validating a PRD with LLM."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return json.dumps({
                "is_valid": True,
                "score": 8.5,
                "missing_sections": [],
                "weak_sections": ["Implementation Constraints"],
                "feedback": "Good PRD overall, but constraints section could be more detailed."
            })
            
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Create a test PRD by using the ProductRequirement class directly
        prd = PRD(
            product_requirement_id="prd-123",
            title="Test PRD",
            description="Test description",
            content="# Test PRD\n\n## Overview\nOverview content\n\n## Key Features\nFeature list\n\n## User Needs\nUser needs\n\n## Success Metrics\nMetrics",
            created_by="agent",
            status="draft",
            related_task_id="task123"
        )
        
        # Call the method
        is_valid = await product_manager_agent.validate_product_requirement_document(prd)
        
        # Verify the result
        assert is_valid is True 