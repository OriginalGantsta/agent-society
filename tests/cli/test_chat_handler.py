"""Tests for CLI chat handler."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_given_query_when_start_session_called_then_invokes_agent_and_exits():
    """Test that providing a query runs once and exits."""
    from agent.cli.chat_handler import CLIChatHandler
    
    # Mock agent
    mock_agent = MagicMock()
    mock_agent.config = MagicMock(name="test-agent")
    
    async def mock_stream(*args, **kwargs):
        yield "Test"
        yield " response"
    
    mock_agent.stream = mock_stream
    
    handler = CLIChatHandler(mock_agent)
    
    with patch("agent.cli.chat_handler.CLIInterface") as MockCLI:
        await handler.start_session(query="test query", thread_id="test-thread")
        
        # Verify UI interactions
        MockCLI.print_separator.assert_called()
        MockCLI.print_system.assert_called()
        MockCLI.print_assistant_prefix.assert_called()
        MockCLI.print_chunk.assert_called()


@pytest.mark.asyncio
async def test_given_no_query_when_start_session_called_then_enters_interactive_mode():
    """Test interactive mode loops until user exits."""
    from agent.cli.chat_handler import CLIChatHandler
    
    mock_agent = MagicMock()
    mock_agent.config = MagicMock(name="test-agent")
    
    async def mock_stream(*args, **kwargs):
        yield "Response"
    
    mock_agent.stream = mock_stream
    
    handler = CLIChatHandler(mock_agent)
    
    with patch("agent.cli.chat_handler.CLIInterface") as MockCLI:
        # Simulate user typing "hello" then "exit"
        MockCLI.get_input.side_effect = ["hello", "exit"]
        
        await handler.start_session()
        
        # Should have called get_input twice
        assert MockCLI.get_input.call_count == 2


@pytest.mark.asyncio
async def test_given_new_command_when_interactive_session_then_creates_new_thread():
    """Test 'new' command creates a new thread."""
    from agent.cli.chat_handler import CLIChatHandler
    
    mock_agent = MagicMock()
    mock_agent.config = MagicMock(name="test-agent")
    
    async def mock_stream(*args, **kwargs):
        yield "Response"
    
    mock_agent.stream = mock_stream
    
    handler = CLIChatHandler(mock_agent)
    
    with patch("agent.cli.chat_handler.CLIInterface") as MockCLI:
        MockCLI.get_input.side_effect = ["new", "quit"]
        
        await handler.start_session()
        
        # Should have printed system message about new session
        system_calls = [call[0][0] for call in MockCLI.print_system.call_args_list]
        assert any("new session" in str(call).lower() for call in system_calls)


@pytest.mark.asyncio
async def test_given_empty_input_when_interactive_session_then_continues():
    """Test that empty input is skipped."""
    from agent.cli.chat_handler import CLIChatHandler
    
    mock_agent = MagicMock()
    mock_agent.config = MagicMock(name="test-agent")
    
    handler = CLIChatHandler(mock_agent)
    
    with patch("agent.cli.chat_handler.CLIInterface") as MockCLI:
        MockCLI.get_input.side_effect = ["", "  ", "quit"]
        
        await handler.start_session()
        
        # Should skip empty inputs and continue
        assert MockCLI.get_input.call_count == 3


@pytest.mark.asyncio
async def test_given_keyboard_interrupt_when_session_active_then_exits_gracefully():
    """Test KeyboardInterrupt exits gracefully."""
    from agent.cli.chat_handler import CLIChatHandler
    
    mock_agent = MagicMock()
    mock_agent.config = MagicMock(name="test-agent")
    
    handler = CLIChatHandler(mock_agent)
    
    with patch("agent.cli.chat_handler.CLIInterface") as MockCLI:
        MockCLI.get_input.side_effect = KeyboardInterrupt()
        
        await handler.start_session()
        
        # Should have printed goodbye message
        goodbye_calls = [call[0][0] for call in MockCLI.print_system.call_args_list]
        assert any("goodbye" in str(call).lower() for call in goodbye_calls)
