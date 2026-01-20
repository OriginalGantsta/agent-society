"""Tests for MCP server implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_given_agent_not_initialized_when_get_agent_called_then_creates_agent():
    """Test that get_agent lazily initializes the agent."""
    from agent.mcp import server
    
    # Reset global agent state
    server._agent = None
    
    mock_agent = MagicMock()
    
    with patch("agent.mcp.server.create_agent_from_args", AsyncMock(return_value=mock_agent)):
        agent = await server.get_agent()
        
        assert agent is mock_agent
        assert server._agent is mock_agent


@pytest.mark.asyncio
async def test_given_agent_already_initialized_when_get_agent_called_then_returns_cached():
    """Test that get_agent returns cached agent on subsequent calls."""
    from agent.mcp import server
    
    mock_agent = MagicMock()
    server._agent = mock_agent
    
    with patch("agent.mcp.server.create_agent_from_args", AsyncMock()) as mock_create:
        agent = await server.get_agent()
        
        assert agent is mock_agent
        # create should not be called since agent exists
        mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_given_message_when_chat_tool_called_then_invokes_agent_invoke():
    """Test that chat tool properly calls agent.invoke."""
    from agent.mcp import server
    
    # Reset global state
    server._agent = None
    
    # Mock agent
    mock_agent = MagicMock()
    mock_agent.invoke = AsyncMock(return_value="This is the agent response")
    
    with patch("agent.mcp.server.create_agent_from_args", AsyncMock(return_value=mock_agent)):
        # Call chat with new simplified signature
        result = await server.chat.fn(message="What is AI?", thread_id="test-thread-123")
        
        # Verify agent.invoke was called correctly
        mock_agent.invoke.assert_called_once_with(
            query="What is AI?",
            thread_id="test-thread-123"
        )
        
        # Verify return format (now just a string)
        assert result == "This is the agent response"


@pytest.mark.asyncio
async def test_given_multiple_calls_when_chat_tool_called_then_uses_same_agent():
    """Test that multiple chat calls use the same agent instance."""
    from agent.mcp import server
    
    # Reset global state
    server._agent = None
    
    mock_agent = MagicMock()
    mock_agent.invoke = AsyncMock(side_effect=["Response 1", "Response 2"])
    
    with patch("agent.mcp.server.create_agent_from_args", AsyncMock(return_value=mock_agent)) as mock_create:
        # First call - access underlying function
        await server.chat.fn(message="First", thread_id="thread-1")
        
        # Second call
        await server.chat.fn(message="Second", thread_id="thread-2")
        
        # create_agent should only be called once
        assert mock_create.call_count == 1
        
        # invoke should be called twice
        assert mock_agent.invoke.call_count == 2


@pytest.mark.asyncio
async def test_given_parse_args_when_called_with_defaults_then_returns_correct_args():
    """Test parse_args with default values."""
    from agent.mcp.server import parse_args
    
    with patch("sys.argv", ["server.py", "--source-type", "filesystem"]):
        args = parse_args()
        
        assert args.config_base_path == "config"
        assert args.source_type == "filesystem"
        assert args.postgres_dsn is None
        assert args.agent_name is None
        assert args.no_mcp is False


@pytest.mark.asyncio
async def test_given_parse_args_when_called_with_postgres_then_parses_correctly():
    """Test parse_args with postgres source."""
    from agent.mcp.server import parse_args
    
    test_args = [
        "server.py",
        "--source-type", "postgres",
        "--postgres-dsn", "postgresql://localhost/test",
        "--agent-name", "test-agent",
        "--no-mcp"
    ]
    
    with patch("sys.argv", test_args):
        args = parse_args()
        
        assert args.source_type == "postgres"
        assert args.postgres_dsn == "postgresql://localhost/test"
        assert args.agent_name == "test-agent"
        assert args.no_mcp is True
