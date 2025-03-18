import pytest
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock

from src.core.agent.ai_agent import AIAgent
from src.core.agent.agent_tool_interface import AgentToolInterface
from src.core.config import Config


class ConcreteAIAgent(AIAgent):
    """Concrete implementation of AIAgent for testing."""
    
    def _setup_prompt(self) -> str:
        """Set up the base prompt for testing."""
        return "You are a test agent. Please respond to the following: {input}"


@pytest.fixture
def setup_env():
    """Set up environment variables for testing."""
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    os.environ["OPENAI_DEFAULT_MODEL"] = "gpt-4-test"
    os.environ["OPENAI_TEMPERATURE"] = "0.5"
    yield
    # Clean up
    del os.environ["OPENAI_API_KEY"]
    del os.environ["OPENAI_DEFAULT_MODEL"]
    del os.environ["OPENAI_TEMPERATURE"]


@pytest.fixture
def mock_chat_openai():
    """Create a mock for ChatOpenAI."""
    with patch("src.core.agent.ai_agent.ChatOpenAI", autospec=True) as mock:
        mock_instance = MagicMock()
        
        # Create a custom ainvoke method that returns a string directly
        async def mock_ainvoke(*args, **kwargs):
            return '{"result": "success", "value": 42}'
            
        # Set the ainvoke method on the mock
        mock_instance.ainvoke = AsyncMock(side_effect=mock_ainvoke)
        
        # Return the mocked instance
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_str_output_parser():
    """Create a mock for StrOutputParser."""
    with patch("src.core.agent.ai_agent.StrOutputParser", autospec=True) as mock:
        mock_instance = MagicMock()
        mock_instance.return_value = "mock response"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config():
    """Create a mock for Config."""
    mock = MagicMock(spec=Config)
    mock.openai_api_key = "mock-api-key"
    mock.openai_default_model = "gpt-4-test"
    mock.openai_temperature = 0.5
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    return {"test_tool": MagicMock()}


@pytest.fixture
def agent(mock_chat_openai, mock_config, mock_tool_registry):
    """Create an instance of ConcreteAIAgent for testing."""
    # Create the agent
    agent = ConcreteAIAgent(
        agent_id="test-agent",
        name="Test Agent",
        description="A test agent",
        tool_registry=mock_tool_registry,
        config=mock_config,
        llm=mock_chat_openai
    )
    
    return agent


class TestAIAgent:
    """Tests for the AIAgent class."""
    
    def test_initialization(self, agent, mock_chat_openai):
        """Test initialization of the agent."""
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.description == "A test agent"
        assert len(agent.tools) == 0  # No tools added yet
        assert agent._base_prompt == "You are a test agent. Please respond to the following: {input}"
    
    def test_add_tool(self, agent, mock_tool_registry):
        """Test adding a tool to the agent."""
        result = agent.add_tool("test_tool")
        assert result is True
        assert "test_tool" in agent.tools
        
        # Test adding a non-existent tool
        result = agent.add_tool("non_existent_tool")
        assert result is False
    
    def test_format_input(self, agent):
        """Test formatting input data."""
        # Test with dictionary
        input_dict = {"key": "value"}
        result = agent._format_input(input_dict)
        assert result == input_dict
        
        # Test with string
        input_str = "test string"
        result = agent._format_input(input_str)
        assert result == {"input": "test string"}
        
        # Test with other types
        input_int = 123
        result = agent._format_input(input_int)
        assert result == {"input": "123"}
    
    def test_parse_output(self, agent):
        """Test parsing output from LLM."""
        # Test with valid JSON
        json_output = '{"key": "value", "list": [1, 2, 3]}'
        result = agent._parse_output(json_output)
        assert result == {"key": "value", "list": [1, 2, 3]}
        
        # Test with invalid JSON
        text_output = "This is not JSON"
        result = agent._parse_output(text_output)
        assert result == {"text": "This is not JSON"}
    
    @pytest.mark.asyncio
    async def test_process(self, agent, mock_chat_openai):
        """Test processing input data."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return '{"result": "success", "value": 42}'
        
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Process some input
        result = await agent.process("test input")
        
        # Verify the result
        assert result == {"result": "success", "value": 42}
        assert mock_chat_openai.ainvoke.called
    
    @pytest.mark.asyncio
    async def test_invoke_llm(self, agent, mock_chat_openai):
        """Test directly invoking the LLM."""
        # Set up custom response for this test
        async def custom_response(*args, **kwargs):
            return '{"direct": "response"}'
        
        mock_chat_openai.ainvoke = AsyncMock(side_effect=custom_response)
        
        # Call invoke_llm
        result = await agent.invoke_llm(
            "Custom prompt: {value}", 
            {"value": "test value"}
        )
        
        # Verify the result
        assert result == {"direct": "response"}
        assert mock_chat_openai.ainvoke.called
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent, mock_chat_openai):
        """Test error handling during processing."""
        # Set up the mock to raise an exception
        mock_chat_openai.ainvoke.side_effect = Exception("Test error")
        
        # Verify that the exception is propagated
        with pytest.raises(Exception) as excinfo:
            await agent.process("test input")
        
        assert "Test error" in str(excinfo.value)
    
    def test_initialization_with_env_vars(self, setup_env):
        """Test initialization with environment variables."""
        # Create agent using environment variables
        agent = ConcreteAIAgent(
            agent_id="env-test",
            name="Env Test",
            description="Testing with env vars"
        )
        
        # Verify the agent was initialized correctly
        assert agent.agent_id == "env-test"
        assert agent._base_prompt == "You are a test agent. Please respond to the following: {input}" 