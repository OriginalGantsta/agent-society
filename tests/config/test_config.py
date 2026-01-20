from agent.config import (
    AgentConfig,
    FilesystemSource,
)
from unittest.mock import patch
import pytest
import json
from pathlib import Path


def test_given_valid_dict_when_from_dict_called_then_returns_config(valid_agent_config_dict):
    config = AgentConfig.from_dict(valid_agent_config_dict)
    
    assert config.name == "test-agent"
    assert config.model_name == "gpt-4"
    assert config.temperature == 0.5
    assert config.system_prompt == "Test system prompt"
    assert config.tool_configs == valid_agent_config_dict["tools"]
    assert config.checkpointer_config == valid_agent_config_dict["checkpointer"]


def test_given_missing_fields_when_from_dict_called_then_uses_defaults():
    empty_dict = {}
    config = AgentConfig.from_dict(empty_dict)
    
    assert config.name == "simple-agent"
    assert config.model_name == "gpt-4"
    assert config.temperature == 0
    assert config.system_prompt == "You are a helpful assistant."
    assert config.tool_configs == []
    assert config.checkpointer_config is None


# Test FilesystemSource MCP injection logic
def test_filesystem_source_with_explicit_tools(tmp_path):
    """Explicit tools in agent.json should be used as-is."""
    agent_file = tmp_path / "agent.json"
    agent_data = {
        "name": "test",
        "tools": [{"type": "custom", "enabled": True}]
    }
    agent_file.write_text(json.dumps(agent_data))
    
    source = FilesystemSource(tmp_path)
    result = source.load(no_mcp=False)
    
    assert result["tools"] == [{"type": "custom", "enabled": True}]


def test_filesystem_source_inject_mcp_when_missing(tmp_path):
    """Should inject MCP when no tools and mcp_servers present."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test"}')
    
    mcp_file = tmp_path / "mcp_servers.json"
    mcp_servers = {"server1": {"command": "test"}}
    mcp_file.write_text(json.dumps(mcp_servers))
    
    source = FilesystemSource(tmp_path)
    result = source.load(no_mcp=False)
    
    assert len(result["tools"]) == 1
    assert result["tools"][0]["type"] == "mcp"
    assert result["tools"][0]["enabled"] is True
    assert result["tools"][0]["servers"] == mcp_servers


def test_filesystem_source_no_mcp_flag_prevents_injection(tmp_path):
    """--no-mcp should prevent MCP injection."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test"}')
    
    mcp_file = tmp_path / "mcp_servers.json"
    mcp_file.write_text('{"server1": {"command": "test"}}')
    
    source = FilesystemSource(tmp_path)
    result = source.load(no_mcp=True)
    
    assert "tools" not in result


def test_filesystem_source_no_mcp_flag_preserves_explicit_tools(tmp_path):
    """--no-mcp should not filter explicit tools from agent.json."""
    agent_file = tmp_path / "agent.json"
    agent_data = {"name": "test", "tools": [{"type": "mcp", "enabled": True}]}
    agent_file.write_text(json.dumps(agent_data))
    
    source = FilesystemSource(tmp_path)
    result = source.load(no_mcp=True)
    
    # Explicit tools should be preserved even with --no-mcp
    assert result["tools"] == [{"type": "mcp", "enabled": True}]


def test_filesystem_source_missing_mcp_servers(tmp_path):
    """Missing mcp_servers.json should proceed without error."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test"}')
    
    source = FilesystemSource(tmp_path)
    result = source.load(no_mcp=False)
    
    assert "tools" not in result


def test_filesystem_source_load_success(tmp_path):
    """FilesystemSource should load valid agent.json."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test", "model": {"name": "gpt-4"}}')
    
    source = FilesystemSource(tmp_path)
    result = source.load()
    
    assert result["name"] == "test"
    assert result["model"]["name"] == "gpt-4"


def test_filesystem_source_missing_directory():
    """FilesystemSource should raise FileNotFoundError for missing directory."""
    source = FilesystemSource(Path("/nonexistent/path"))
    
    with pytest.raises(FileNotFoundError, match="Config directory does not exist"):
        source.load()


def test_filesystem_source_missing_file(tmp_path):
    """FilesystemSource should raise FileNotFoundError for missing agent.json."""
    source = FilesystemSource(tmp_path)
    
    with pytest.raises(FileNotFoundError, match="Required agent config not found"):
        source.load()


# Integration tests for full load flow
def test_full_load_flow_with_mcp(tmp_path):
    """Test full configuration loading flow with MCP injection."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test-agent", "model": {"name": "gpt-4", "temperature": 0.7}, "prompt": "Test"}')
    
    mcp_file = tmp_path / "mcp_servers.json"
    mcp_file.write_text('{"server1": {"command": "npx", "args": ["-y", "@test/server"]}}')
    
    source = FilesystemSource(tmp_path)
    config_data = source.load(no_mcp=False)
    config = AgentConfig.from_dict(config_data)
    
    assert config.name == "test-agent"
    assert config.model_name == "gpt-4"
    assert config.temperature == 0.7
    assert len(config.tool_configs) == 1
    assert config.tool_configs[0]["type"] == "mcp"
    assert config.tool_configs[0]["servers"]["server1"]["command"] == "npx"


def test_full_load_flow_without_mcp(tmp_path):
    """Test full configuration loading flow with --no-mcp."""
    agent_file = tmp_path / "agent.json"
    agent_file.write_text('{"name": "test-agent", "model": {"name": "gpt-4"}}')
    
    mcp_file = tmp_path / "mcp_servers.json"
    mcp_file.write_text('{"server1": {"command": "test"}}')
    
    source = FilesystemSource(tmp_path)
    config_data = source.load(no_mcp=True)
    config = AgentConfig.from_dict(config_data)
    
    assert config.name == "test-agent"
    assert config.tool_configs == []  # No MCP injection


def test_full_load_flow_with_explicit_tools(tmp_path):
    """Test that explicit tools in agent.json are preserved."""
    agent_file = tmp_path / "agent.json"
    agent_data = {
        "name": "test-agent",
        "model": {"name": "gpt-4"},
        "tools": [{"type": "custom", "enabled": True, "name": "my-tool"}]
    }
    agent_file.write_text(json.dumps(agent_data))
    
    source = FilesystemSource(tmp_path)
    config_data = source.load(no_mcp=False)
    config = AgentConfig.from_dict(config_data)
    
    assert config.name == "test-agent"
    assert len(config.tool_configs) == 1
    assert config.tool_configs[0]["type"] == "custom"
    assert config.tool_configs[0]["name"] == "my-tool"

