import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agent.core import AgentFactory

@pytest.mark.asyncio
async def test_given_config_when_create_called_then_creates_graph(valid_agent_config):
    with patch("agent.core.agent.LLMResolver") as MockLLMResolver, \
         patch("agent.core.agent.create_agent") as mock_create_agent, \
         patch("agent.core.agent.MiddlewareResolver") as MockMiddlewareResolver, \
         patch("agent.core.agent.ToolResolver") as MockToolResolver, \
         patch("agent.core.agent.CheckpointerResolver") as MockCheckpointerResolver:
        
        mock_llm = MagicMock()
        MockLLMResolver.resolve.return_value = mock_llm
        MockMiddlewareResolver.resolve_all.return_value = []
        MockToolResolver.resolve_all = AsyncMock(return_value=["tool"])
        mock_checkpointer = MagicMock()
        MockCheckpointerResolver.resolve.return_value = mock_checkpointer
        
        agent = await AgentFactory.create(valid_agent_config)
        
        MockLLMResolver.resolve.assert_called_once_with(
            valid_agent_config.model_name, 
            valid_agent_config.temperature
        )
        mock_create_agent.assert_called_once()
        MockMiddlewareResolver.resolve_all.assert_called_once_with(valid_agent_config.middleware_configs)
        MockToolResolver.resolve_all.assert_awaited_once_with(valid_agent_config.tool_configs)
        MockCheckpointerResolver.resolve.assert_called_once_with(valid_agent_config.checkpointer_config)
        assert agent.graph is not None

@pytest.mark.asyncio
async def test_given_query_when_stream_called_then_yields_response_tokens(valid_agent_config):
    """Test that stream() yields response tokens correctly."""
    with patch("agent.core.agent.LLMResolver"), \
         patch("agent.core.agent.create_agent") as mock_create_agent, \
         patch("agent.core.agent.MiddlewareResolver") as MockMiddlewareResolver, \
         patch("agent.core.agent.ToolResolver") as MockToolResolver, \
         patch("agent.core.agent.CheckpointerResolver") as MockCheckpointerResolver:
        
        # Setup mocks
        mock_graph = MagicMock()
        mock_create_agent.return_value = mock_graph
        MockMiddlewareResolver.resolve_all.return_value = []
        MockToolResolver.resolve_all = AsyncMock(return_value=["tool"])
        MockCheckpointerResolver.resolve.return_value = MagicMock()

        # Create agent
        agent = await AgentFactory.create(valid_agent_config)
        
        # Mock astream to yield tokens
        async def async_gen(*args, **kwargs):
            mock_chunk1 = MagicMock()
            mock_chunk1.content = "Hello"
            mock_chunk2 = MagicMock()
            mock_chunk2.content = " World"
            
            metadata = {"langgraph_node": "agent"}
            yield (mock_chunk1, metadata)
            yield (mock_chunk2, metadata)
            
        mock_graph.astream = async_gen
        
        # Call stream and collect tokens
        tokens = []
        async for token in agent.stream("test query", "thread-123"):
            tokens.append(token)
        
        # Verify tokens
        assert tokens == ["Hello", " World"]


@pytest.mark.asyncio
async def test_given_query_when_invoke_called_then_returns_complete_response(valid_agent_config):
    """Test that invoke() returns the complete response."""
    with patch("agent.core.agent.LLMResolver"), \
         patch("agent.core.agent.create_agent") as mock_create_agent, \
         patch("agent.core.agent.MiddlewareResolver") as MockMiddlewareResolver, \
         patch("agent.core.agent.ToolResolver") as MockToolResolver, \
         patch("agent.core.agent.CheckpointerResolver") as MockCheckpointerResolver:
        
        # Setup mocks
        mock_graph = MagicMock()
        mock_create_agent.return_value = mock_graph
        MockMiddlewareResolver.resolve_all.return_value = []
        MockToolResolver.resolve_all = AsyncMock(return_value=["tool"])
        MockCheckpointerResolver.resolve.return_value = MagicMock()

        # Create agent
        agent = await AgentFactory.create(valid_agent_config)
        
        # Mock astream
        async def async_gen(*args, **kwargs):
            mock_chunk1 = MagicMock()
            mock_chunk1.content = "Complete"
            mock_chunk2 = MagicMock()
            mock_chunk2.content = " response"
            
            metadata = {"langgraph_node": "agent"}
            yield (mock_chunk1, metadata)
            yield (mock_chunk2, metadata)
            
        mock_graph.astream = async_gen
        
        # Call invoke
        response = await agent.invoke("test query", "thread-123")
        
        # Verify complete response
        assert response == "Complete response"

