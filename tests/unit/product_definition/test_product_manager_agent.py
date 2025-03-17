"""
Unit tests for the Product Manager Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.task_management.domain.entities.task import Task
from src.task_management.domain.value_objects.task_status import TaskStatus
from src.task_management.domain.value_objects.task_priority import TaskPriority
from src.product_definition.domain.entities.product_requirement import ProductRequirement
from src.product_definition.agents.product_manager_agent import ProductManagerAgent
from src.core.agent.tool_registry import ToolRegistry


@pytest.fixture
def mock_task_service():
    """Create a mock task service."""
    task_service = AsyncMock()
    task_service.update_task_status = AsyncMock()
    task_service.add_comment = AsyncMock()
    return task_service


@pytest.fixture
def mock_product_requirement_repository():
    """Create a mock product requirement repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.find_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    registry = MagicMock(spec=ToolRegistry)
    registry.get_tool = MagicMock()
    registry.list_tools = MagicMock(return_value=[])
    return registry


@pytest.fixture
def product_manager_agent(mock_task_service, mock_product_requirement_repository, mock_tool_registry):
    """Create a Product Manager Agent instance for testing."""
    return ProductManagerAgent(
        task_service=mock_task_service,
        product_requirement_repository=mock_product_requirement_repository,
        tool_registry=mock_tool_registry
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task = Task(
        task_id="task-1",
        title="Create a PRD for new user onboarding",
        description="We need a PRD for a new user onboarding flow. The onboarding should be simple and guide users through the first steps of using our product. Target audience: non-technical users. Product type: web app. Estimated effort: medium.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.ASSIGNED,
        created_by="test_user",
        assignee="pma-agent"
    )
    # Add tags for the information that would normally be in metadata
    task.tags = ["product_type:web_app", "target_audience:non-technical users", "estimated_effort:medium"]
    return task


# Helper function to check if a specific update_task_status call was made
def assert_status_update_called_with(mock, task_id, new_status, changed_by, reason=None):
    """Check if update_task_status was called with specific parameters."""
    for call in mock.mock_calls:
        kwargs = call[2]
        if kwargs.get('task_id') == task_id and kwargs.get('new_status') == new_status and kwargs.get('changed_by') == changed_by:
            if reason is None or kwargs.get('reason') == reason:
                return True
    assert False, f"update_task_status not called with task_id={task_id}, new_status={new_status}, changed_by={changed_by}, reason={reason}"


@pytest.mark.asyncio
async def test_process_task_basic_flow(product_manager_agent, mock_task_service, mock_product_requirement_repository, sample_task):
    """Test the basic flow of processing a task."""
    # Set the return value for update_task_status to return the task
    mock_task_service.update_task_status.return_value = sample_task
    
    # Mock the clarity analysis to return high clarity and completeness
    with patch.object(
        product_manager_agent, 'analyze_user_request', return_value={
            "clarity_score": 8.5,
            "completeness_score": 9.0,
            "key_features": ["Simple onboarding flow", "First-time user guide"],
            "target_audience": "non-technical users",
            "product_type": "web_app"
        }
    ), patch.object(
        product_manager_agent, 'determine_if_clarification_needed', return_value=False
    ), patch.object(
        product_manager_agent, 'create_product_requirement_document', return_value=ProductRequirement(
            product_requirement_id="prd-1",
            title="New User Onboarding PRD",
            description="PRD for new user onboarding flow",
            content="# New User Onboarding\n\n## Overview\nThis PRD describes the new user onboarding process...",
            created_by="pma-agent",
            status="draft",
            related_task_id="task-1"
        )
    ), patch.object(
        product_manager_agent, 'validate_product_requirement_document', return_value=True
    ):
        # Process the task
        result = await product_manager_agent.process_task(sample_task)
        
        # Verify that update_task_status was called to mark the task as in progress
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.IN_PROGRESS.value,
            changed_by=product_manager_agent.agent_id,
            reason="Starting to analyze request"
        )
        
        # Verify that the product requirement was created
        mock_product_requirement_repository.create.assert_called_once()
        
        # Verify that update_task_status was called to mark the task as completed
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.COMPLETED.value,
            changed_by=product_manager_agent.agent_id,
            reason="Product requirement document created successfully"
        )
        
        # Verify that the task was returned
        assert result == sample_task


@pytest.mark.asyncio
async def test_process_task_with_clarification(product_manager_agent, mock_task_service, sample_task):
    """Test processing a task that needs clarification."""
    # Set the return value for update_task_status to return the task
    mock_task_service.update_task_status.return_value = sample_task
    
    # Mock the clarity analysis to return low clarity and completeness
    with patch.object(
        product_manager_agent, 'analyze_user_request', return_value={
            "clarity_score": 4.5,
            "completeness_score": 3.0,
            "key_features": [],
            "target_audience": "unknown",
            "product_type": "web_app"
        }
    ), patch.object(
        product_manager_agent, 'determine_if_clarification_needed', return_value=True
    ), patch.object(
        product_manager_agent, 'generate_clarification_questions', return_value=[
            "What specific features should be included in the onboarding?",
            "What is the target audience for this onboarding?",
            "Are there any specific metrics we should track during onboarding?"
        ]
    ):
        # Process the task
        result = await product_manager_agent.process_task(sample_task)
        
        # Verify that update_task_status was called to mark the task as in progress
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.IN_PROGRESS.value,
            changed_by=product_manager_agent.agent_id,
            reason="Starting to analyze request"
        )
        
        # Verify that update_task_status was called to mark the task as needing clarification
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.BLOCKED.value,  # Using BLOCKED instead of CLARIFICATION_NEEDED
            changed_by=product_manager_agent.agent_id,
            reason="Additional information needed to create PRD"
        )
        
        # Verify that add_comment was called with the clarification questions
        mock_task_service.add_comment.assert_called_with(
            task_id="task-1",
            comment="Please provide clarification on the following:\n1. What specific features should be included in the onboarding?\n2. What is the target audience for this onboarding?\n3. Are there any specific metrics we should track during onboarding?",
            created_by=product_manager_agent.agent_id
        )
        
        # Verify that the task was returned
        assert result == sample_task


@pytest.mark.asyncio
async def test_process_task_validation_failure(product_manager_agent, mock_task_service, mock_product_requirement_repository, sample_task):
    """Test processing a task where the PRD validation fails."""
    # Set the return value for update_task_status to return the task
    mock_task_service.update_task_status.return_value = sample_task
    
    # Mock the clarity analysis to return high clarity and completeness
    with patch.object(
        product_manager_agent, 'analyze_user_request', return_value={
            "clarity_score": 8.5,
            "completeness_score": 9.0,
            "key_features": ["Simple onboarding flow", "First-time user guide"],
            "target_audience": "non-technical users",
            "product_type": "web_app"
        }
    ), patch.object(
        product_manager_agent, 'determine_if_clarification_needed', return_value=False
    ), patch.object(
        product_manager_agent, 'create_product_requirement_document', return_value=ProductRequirement(
            product_requirement_id="prd-1",
            title="New User Onboarding PRD",
            description="PRD for new user onboarding flow",
            content="# New User Onboarding\n\n## Overview\nThis PRD describes the new user onboarding process...",
            created_by="pma-agent",
            status="draft",
            related_task_id="task-1"
        )
    ), patch.object(
        product_manager_agent, 'validate_product_requirement_document', return_value=False
    ):
        # Process the task
        result = await product_manager_agent.process_task(sample_task)
        
        # Verify that update_task_status was called to mark the task as in progress
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.IN_PROGRESS.value,
            changed_by=product_manager_agent.agent_id,
            reason="Starting to analyze request"
        )
        
        # Verify that update_task_status was called to mark the task as needing revision
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.REVIEW.value,  # Using REVIEW instead of NEEDS_REVISION
            changed_by=product_manager_agent.agent_id,
            reason="Created PRD does not meet quality standards"
        )
        
        # Verify that the task was returned
        assert result == sample_task


@pytest.mark.asyncio
async def test_analyze_user_request(product_manager_agent, sample_task):
    """Test analyzing a user request."""
    # Analyze the request
    analysis = await product_manager_agent.analyze_user_request(sample_task)
    
    # Verify that the analysis contains the expected fields
    assert "clarity_score" in analysis
    assert "completeness_score" in analysis
    assert "key_features" in analysis
    assert "target_audience" in analysis
    assert "product_type" in analysis
    
    # The description and tags should contain the information to be extracted
    assert analysis["target_audience"] != "unknown"
    assert analysis["product_type"] != "unknown"


@pytest.mark.asyncio
async def test_determine_if_clarification_needed(product_manager_agent):
    """Test determining if clarification is needed based on analysis."""
    # Test with low clarity and completeness
    low_analysis = {
        "clarity_score": 3.5,
        "completeness_score": 4.0,
        "key_features": [],
        "target_audience": "unknown",
        "product_type": "web_app",
        "missing_information": ["target_audience", "key_features"]
    }
    
    # Test with high clarity and completeness
    high_analysis = {
        "clarity_score": 8.5,
        "completeness_score": 9.0,
        "key_features": ["Feature 1", "Feature 2"],
        "target_audience": "developers",
        "product_type": "web_app",
        "missing_information": []
    }
    
    # Check the results
    assert await product_manager_agent.determine_if_clarification_needed(low_analysis) is True
    assert await product_manager_agent.determine_if_clarification_needed(high_analysis) is False


@pytest.mark.asyncio
async def test_generate_clarification_questions(product_manager_agent, sample_task):
    """Test generating clarification questions."""
    # Set up the analysis with missing information
    analysis = {
        "clarity_score": 4.5,
        "completeness_score": 3.0,
        "key_features": [],
        "target_audience": "unknown",
        "product_type": "web_app",
        "missing_information": ["target_audience", "key_features", "constraints"]
    }
    
    # Generate questions
    questions = await product_manager_agent.generate_clarification_questions(sample_task, analysis)
    
    # Verify that questions were generated for the missing information
    assert len(questions) > 0
    assert any("target audience" in q.lower() for q in questions)
    assert any("features" in q.lower() for q in questions)
    assert any("constraints" in q.lower() for q in questions)


@pytest.mark.asyncio
async def test_create_product_requirement_document(product_manager_agent, sample_task):
    """Test creating a product requirement document."""
    # Set up the analysis
    analysis = {
        "clarity_score": 8.5,
        "completeness_score": 9.0,
        "key_features": ["Simple onboarding flow", "First-time user guide"],
        "target_audience": "non-technical users",
        "product_type": "web_app"
    }
    
    # Create the PRD
    prd = await product_manager_agent.create_product_requirement_document(sample_task, analysis)
    
    # Verify that the PRD was created with the expected information
    assert prd.product_requirement_id is not None
    assert prd.title is not None
    assert prd.description is not None
    assert prd.content is not None
    assert prd.created_by == product_manager_agent.agent_id
    assert prd.related_task_id == sample_task.task_id
    
    # Verify that the content includes information from the analysis
    assert "non-technical users" in prd.content
    assert "web_app" in prd.content or "web app" in prd.content
    assert "Simple onboarding flow" in prd.content
    assert "First-time user guide" in prd.content


@pytest.mark.asyncio
async def test_validate_product_requirement_document(product_manager_agent):
    """Test validating a product requirement document."""
    # Create a valid PRD
    valid_prd = ProductRequirement(
        product_requirement_id="prd-1",
        title="Valid PRD",
        description="This is a valid PRD",
        content="""# Valid PRD

## Overview
This is an overview section.

## Key Features
- Feature 1
- Feature 2

## User Needs
- Need 1
- Need 2

## Success Metrics
- Metric 1
- Metric 2
""",
        created_by="pma-agent",
        status="draft",
        related_task_id="task-1"
    )
    valid_prd.extract_sections()
    
    # Create an invalid PRD (too short, missing sections)
    invalid_prd = ProductRequirement(
        product_requirement_id="prd-2",
        title="Invalid PRD",
        description="This is an invalid PRD",
        content="# Invalid PRD\n\nToo short.",
        created_by="pma-agent",
        status="draft",
        related_task_id="task-2"
    )
    invalid_prd.extract_sections()
    
    # Validate the PRDs
    is_valid = await product_manager_agent.validate_product_requirement_document(valid_prd)
    is_invalid = await product_manager_agent.validate_product_requirement_document(invalid_prd)
    
    # Verify that validation returned the expected results
    assert is_valid is True
    assert is_invalid is False


@pytest.mark.asyncio
async def test_process_task_with_error_handling(product_manager_agent, mock_task_service, sample_task):
    """Test error handling during task processing."""
    # Set the return value for update_task_status to return the task
    mock_task_service.update_task_status.return_value = sample_task
    
    # Mock analyze_user_request to raise an exception
    with patch.object(
        product_manager_agent, 'analyze_user_request', side_effect=Exception("Test error")
    ):
        # Process the task
        result = await product_manager_agent.process_task(sample_task)
        
        # Verify that update_task_status was called to mark the task as failed
        assert_status_update_called_with(
            mock_task_service.update_task_status,
            task_id="task-1",
            new_status=TaskStatus.CANCELED.value,  # Using CANCELED instead of FAILED
            changed_by=product_manager_agent.agent_id,
            reason="Error processing task: Test error"
        )
        
        # Verify that add_comment was called with the error details
        mock_task_service.add_comment.assert_called_with(
            task_id="task-1",
            comment="An error occurred while processing this task: Test error",
            created_by=product_manager_agent.agent_id
        )
        
        # Verify that the task was returned
        assert result == sample_task 