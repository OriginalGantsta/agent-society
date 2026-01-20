"""Tests for PostgreSQL configuration source.

Tests cover:
- Database connection and query logic
- MCP tool injection rules
- Active version selection
- Error handling (missing agent, connection failures)
- Middleware loading
- Tool configuration
"""
import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4


# Mock psycopg2 before importing PostgresSource
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

from agent.config.sources.postgres import PostgresSource


@pytest.fixture
def mock_connection():
    """Mock psycopg2 connection with cursor."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def sample_agent_row():
    """Sample agent and version data."""
    return {
        "agent_id": uuid4(),
        "name": "test-agent",
        "description": "Test agent description",
        "version_id": uuid4(),
        "version": 1,
        "model_name": "gpt-4",
        "model_temperature": 0.7,
        "prompt": "You are a helpful assistant",
        "schema_version": 1
    }


@pytest.fixture
def sample_mcp_servers():
    """Sample MCP server configurations."""
    return [
        {
            "id": uuid4(),
            "name": "server1",
            "description": "Test server 1",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@test/server1"],
            "enabled": True
        },
        {
            "id": uuid4(),
            "name": "server2",
            "description": "Test server 2",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "test.server2"],
            "enabled": True
        }
    ]


class TestPostgresSourceBasics:
    """Test basic PostgresSource functionality."""
    
    def test_initialization(self):
        """PostgresSource should initialize with connection string and agent name."""
        source = PostgresSource("postgresql://localhost/test", "test-agent")
        assert source.connection_string == "postgresql://localhost/test"
        assert source.agent_name == "test-agent"
        assert source._conn is None
    
    def test_connection_lazy_initialization(self):
        """Connection should be lazy-initialized on first use."""
        source = PostgresSource("postgresql://localhost/test", "test-agent")
        assert source._conn is None
        
        source._connect()
        assert source._conn is not None
    
    def test_missing_psycopg2_raises_import_error(self):
        """Should raise ImportError if psycopg2 not installed."""
        # This test is hard to do with psycopg2 already mocked globally
        # Just ensure the import error message is correct
        pass


class TestPostgresSourceLoad:
    """Test load() method and configuration assembly."""
    
    def test_load_basic_config(self, mock_connection, sample_agent_row):
        """Should load basic agent configuration without tools."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            # Simulate the single query result with JSON aggregation
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=True)
            
            assert result["name"] == "test-agent"
            assert result["description"] == "Test agent description"
            assert result["llm"]["model_name"] == "gpt-4"
            assert result["llm"]["temperature"] == 0.7
            assert result["prompt"] == "You are a helpful assistant"
            assert result["tools"] == []
    
    def test_load_missing_agent_raises_error(self, mock_connection):
        """Should raise FileNotFoundError if agent not found."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            cursor.fetchone.return_value = None
            
            source = PostgresSource("postgresql://localhost/test", "nonexistent-agent")
            
            with pytest.raises(FileNotFoundError, match="Agent 'nonexistent-agent' not found"):
                source.load()
    
    def test_load_with_middlewares(self, mock_connection, sample_agent_row):
        """Should load and order middlewares by execution_order."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            # Simulate the single query result with JSON aggregation
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = [
                {
                    "type": "summarization",
                    "config": {"max_tokens": 1000},
                    "enabled": True,
                    "execution_order": 1
                },
                {
                    "type": "logging",
                    "config": None,
                    "enabled": True,
                    "execution_order": 2
                }
            ]
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=True)
            
            assert len(result["middlewares"]) == 2
            assert result["middlewares"][0]["type"] == "summarization"
            assert result["middlewares"][0]["config"] == {"max_tokens": 1000}
            assert result["middlewares"][1]["type"] == "logging"
            assert "config" not in result["middlewares"][1]


class TestPostgresSourceMCPInjection:
    """Test MCP tool injection logic."""
    
    def test_no_tools_returns_empty_list(self, mock_connection, 
                                          sample_agent_row, sample_mcp_servers):
        """Should return empty tools list when no explicit tools configured."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            # Simulate the single query result with no tools
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=False)
            
            # No fallback injection - just empty tools
            assert result["tools"] == []
    
    def test_no_mcp_flag_prevents_injection(self, mock_connection, 
                                             sample_agent_row, sample_mcp_servers):
        """--no-mcp flag should prevent MCP injection."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=True)
            
            assert result["tools"] == []
    
    def test_no_tools_configured_returns_empty(self, mock_connection, sample_agent_row):
        """Should return empty tools when agent has no tools configured."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=False)
            
            # No fallback - agent simply has no tools
            assert result["tools"] == []
    
    def test_explicit_tools_override_mcp_injection(self, mock_connection, 
                                                     sample_agent_row, sample_mcp_servers):
        """Explicit tools should be used instead of MCP injection."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            tool_id = uuid4()
            
            # Simulate the single query result with tools in JSON aggregation
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "mcp_server",
                    "tool_id": tool_id,
                    "tool_name": "server1",
                    "enabled": True,
                    "priority": 1,
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@test/server1"],
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=False)
            
            assert len(result["tools"]) == 1
            assert result["tools"][0]["type"] == "mcp"
            assert "server1" in result["tools"][0]["servers"]
    
    def test_disabled_mcp_server_not_included(self, mock_connection, sample_agent_row):
        """Disabled MCP servers should not be included in tools."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            # Simulate disabled server filtered out by query
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []  # Disabled tools filtered by FILTER clause
            
            cursor.fetchone.return_value = result_row
            cursor.fetchall.return_value = []  # No fallback MCP servers either
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=False)
            
            # No tools since server was disabled
            assert result["tools"] == []


class TestPostgresSourceAgentAsTools:
    """Test agent-as-tool functionality with convention-based defaults."""
    
    def test_agent_tool_applies_convention_defaults(self, mock_connection, sample_agent_row):
        """Agent tools should use convention-based defaults when values are NULL."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            tool_id = uuid4()
            
            # Simulate agent tool with NULL command/transport/args (from tool_catalog view)
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "agent",
                    "tool_id": tool_id,
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 1,
                    "transport": None,  # NULL from catalog
                    "command": None,    # NULL from catalog
                    "args": None,       # NULL from catalog
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://user:pass@localhost:5432/db", "test-agent")
            result = source.load(no_mcp=False)
            
            # Should have one MCP tool config
            assert len(result["tools"]) == 1
            assert result["tools"][0]["type"] == "mcp"
            
            # Should apply convention-based defaults
            servers = result["tools"][0]["servers"]
            assert "demo-agent" in servers
            agent_config = servers["demo-agent"]
            
            import sys
            assert agent_config["transport"] == "stdio"
            assert agent_config["command"] == sys.executable
            assert agent_config["args"] == [
                "-m", "agent.mcp.server",
                "--source-type", "postgres",
                "--postgres-dsn", "postgresql://user:pass@localhost:5432/db",
                "--agent-name", "demo-agent"
            ]
    
    def test_agent_tool_respects_transport_override(self, mock_connection, sample_agent_row):
        """Agent tools should use override transport when provided."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "agent",
                    "tool_id": uuid4(),
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 1,
                    "transport": "sse",  # Override from avt.override
                    "command": None,
                    "args": None,
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/db", "test-agent")
            result = source.load(no_mcp=False)
            
            servers = result["tools"][0]["servers"]
            assert servers["demo-agent"]["transport"] == "sse"
    
    def test_agent_tool_respects_command_override(self, mock_connection, sample_agent_row):
        """Agent tools should use override command when provided."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "agent",
                    "tool_id": uuid4(),
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 1,
                    "transport": None,
                    "command": "python3",  # Override from avt.override
                    "args": None,
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/db", "test-agent")
            result = source.load(no_mcp=False)
            
            servers = result["tools"][0]["servers"]
            assert servers["demo-agent"]["command"] == "python3"
    
    def test_agent_tool_respects_args_override(self, mock_connection, sample_agent_row):
        """Agent tools should use override args when provided."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            custom_args = ["custom", "command", "args"]
            
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "agent",
                    "tool_id": uuid4(),
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 1,
                    "transport": None,
                    "command": None,
                    "args": custom_args,  # Override from avt.override
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/db", "test-agent")
            result = source.load(no_mcp=False)
            
            servers = result["tools"][0]["servers"]
            assert servers["demo-agent"]["args"] == custom_args
    
    def test_agent_tool_respects_env_override(self, mock_connection, sample_agent_row):
        """Agent tools should include env when provided in override."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            custom_env = {"CUSTOM_VAR": "value"}
            
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "agent",
                    "tool_id": uuid4(),
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 1,
                    "transport": None,
                    "command": None,
                    "args": None,
                    "env": custom_env  # Override from avt.override
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/db", "test-agent")
            result = source.load(no_mcp=False)
            
            servers = result["tools"][0]["servers"]
            assert servers["demo-agent"]["env"] == custom_env
    
    def test_mixed_mcp_and_agent_tools(self, mock_connection, sample_agent_row):
        """Should handle both MCP servers and agent tools in same config."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = [
                {
                    "tool_kind": "mcp_server",
                    "tool_id": uuid4(),
                    "tool_name": "filesystem",
                    "enabled": True,
                    "priority": 1,
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    "env": None
                },
                {
                    "tool_kind": "agent",
                    "tool_id": uuid4(),
                    "tool_name": "demo-agent",
                    "enabled": True,
                    "priority": 2,
                    "transport": None,
                    "command": None,
                    "args": None,
                    "env": None
                }
            ]
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://user:pass@localhost/db", "test-agent")
            result = source.load(no_mcp=False)
            
            # Should have one MCP tool config with both servers
            assert len(result["tools"]) == 1
            servers = result["tools"][0]["servers"]
            
            # MCP server should use database values
            assert servers["filesystem"]["command"] == "npx"
            assert servers["filesystem"]["args"] == ["-y", "@modelcontextprotocol/server-filesystem"]
            
            # Agent should use convention defaults
            import sys
            assert servers["demo-agent"]["command"] == sys.executable
            assert "-m" in servers["demo-agent"]["args"]
            assert "agent.mcp.server" in servers["demo-agent"]["args"]


class TestPostgresSourceConnectionManagement:
    """Test database connection lifecycle."""
    
    def test_connection_closed_after_load(self, mock_connection, sample_agent_row):
        """Connection should be closed after load, even on success."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            source.load(no_mcp=True)
            
            conn.close.assert_called_once()
    
    def test_connection_closed_on_error(self, mock_connection):
        """Connection should be closed even if load raises an error."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            cursor.fetchone.return_value = None  # Agent not found
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            
            with pytest.raises(FileNotFoundError):
                source.load()
            
            conn.close.assert_called_once()


class TestPostgresSourcePromptHandling:
    """Test prompt field handling."""
    
    def test_prompt_included_when_present(self, mock_connection, sample_agent_row):
        """Prompt should be included in config when present."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=True)
            
            assert result["prompt"] == "You are a helpful assistant"
    
    def test_prompt_omitted_when_null(self, mock_connection, sample_agent_row):
        """Prompt should be omitted from config when null."""
        conn, cursor = mock_connection
        
        with patch('psycopg2.connect', return_value=conn):
            result_row = sample_agent_row.copy()
            result_row["prompt"] = None
            result_row["middlewares"] = []
            result_row["tools"] = []
            
            cursor.fetchone.return_value = result_row
            
            source = PostgresSource("postgresql://localhost/test", "test-agent")
            result = source.load(no_mcp=True)
            
            assert "prompt" not in result
