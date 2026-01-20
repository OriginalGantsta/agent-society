import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import argparse
from agent.cli.cli import main, parse_args

@pytest.mark.asyncio
async def test_given_missing_config_file_when_load_configs_called_then_raises_error():
    from agent.config import FilesystemSource
    
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            source = FilesystemSource(Path("nonexistent"))
            source.load()

@pytest.mark.asyncio
async def test_given_no_mcp_flag_when_main_called_then_skips_mcp_loading():
    # Mock args
    mock_args = MagicMock()
    mock_args.no_mcp = True
    mock_args.query = None
    mock_args.thread_id = None
    mock_args.config_base_path = "config/path"
    mock_args.source_type = "filesystem"
    
    # Mock deps
    with patch("agent.cli.cli.parse_args", return_value=mock_args), \
         patch("agent.cli.cli.load_dotenv"), \
         patch("agent.bootstrap.AgentFactory") as MockAgentFactory, \
         patch("agent.bootstrap.FilesystemSource") as MockSource, \
         patch("agent.bootstrap.AgentConfig") as MockAgentConfig, \
         patch("agent.bootstrap.configure_langsmith"), \
         patch("agent.cli.cli.CLIChatHandler") as MockChatHandler:
             
        # Setup mocks
        mock_source_instance = MagicMock()
        mock_config_data = {"name": "test", "model": {"name": "gpt-4"}}
        mock_source_instance.load.return_value = mock_config_data
        MockSource.return_value = mock_source_instance
        
        mock_config = MagicMock()
        MockAgentConfig.from_dict.return_value = mock_config
        
        # Make AgentFactory.create awaitable and return the instance
        mock_agent_instance = MagicMock()
        
        async def async_create(*args, **kwargs):
            return mock_agent_instance
            
        MockAgentFactory.create.side_effect = async_create
        
        # Mock chat handler
        mock_handler = MagicMock()
        mock_handler.start_session = AsyncMock()
        MockChatHandler.return_value = mock_handler
        
        await main()
        
        # Assertions - verify load was called with no_mcp=True
        mock_source_instance.load.assert_called_once_with(no_mcp=True)
        MockAgentConfig.from_dict.assert_called_once_with(mock_config_data)
        MockAgentFactory.create.assert_called_once_with(mock_config)
        MockChatHandler.assert_called_once_with(mock_agent_instance)
        mock_handler.start_session.assert_called_once()

@pytest.mark.asyncio
async def test_given_query_arg_when_main_called_then_invokes_agent_chat_with_query():
    # Mock args
    mock_args = MagicMock()
    mock_args.query = "test query"
    mock_args.thread_id = "test-thread"
    mock_args.config_base_path = "config/path"
    mock_args.no_mcp = False
    mock_args.source_type = "filesystem"
    
    # Mock deps
    with patch("agent.cli.cli.parse_args", return_value=mock_args), \
         patch("agent.cli.cli.load_dotenv"), \
         patch("agent.bootstrap.AgentFactory") as MockAgentFactory, \
         patch("agent.bootstrap.FilesystemSource") as MockSource, \
         patch("agent.bootstrap.AgentConfig") as MockAgentConfig, \
         patch("agent.bootstrap.configure_langsmith"), \
         patch("agent.cli.cli.CLIChatHandler") as MockChatHandler:
             
        # Setup mocks
        mock_source_instance = MagicMock()
        mock_config_data = {"name": "test", "model": {"name": "gpt-4"}}
        mock_source_instance.load.return_value = mock_config_data
        MockSource.return_value = mock_source_instance
        
        mock_config = MagicMock()
        MockAgentConfig.from_dict.return_value = mock_config
        
        mock_agent_instance = MagicMock()
        async def async_create(*args, **kwargs): return mock_agent_instance
        MockAgentFactory.create.side_effect = async_create
        
        # Mock chat handler
        mock_handler = MagicMock()
        mock_handler.start_session = AsyncMock()
        MockChatHandler.return_value = mock_handler
        
        await main()
        
        # Assert chat handler called with query and thread_id
        MockChatHandler.assert_called_once_with(mock_agent_instance)
        mock_handler.start_session.assert_called_once_with(query="test query", thread_id="test-thread")

def test_given_no_args_when_parse_args_called_then_uses_defaults():
    with patch("sys.argv", ["cli.py"]):
        args = parse_args()
        
        assert args.query is None
        assert args.config_base_path == "config"
        assert args.no_mcp is False
        assert args.interactive is False
        assert args.trace is False
        assert args.thread_id is None

def test_given_all_args_when_parse_args_called_then_parses_correctly():
    test_args = [
        "cli.py", 
        "some query",
        "--config", "custom/path",
        "--no-mcp",
        "--interactive",
        "--trace",
        "--thread-id", "123"
    ]
    
    with patch("sys.argv", test_args):
        args = parse_args()
        
        assert args.query == "some query"
        assert args.config_base_path == "custom/path"
        assert args.no_mcp is True
        assert args.interactive is True
        assert args.trace is True
        assert args.thread_id == "123"
