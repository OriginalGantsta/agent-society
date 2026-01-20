import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_given_no_configs_when_resolve_all_called_then_returns_empty_list():
    from agent.infrastructure.tools.resolver import ToolResolver

    tools = await ToolResolver.resolve_all([])

    assert tools == []


@pytest.mark.asyncio
async def test_given_none_configs_when_resolve_all_called_then_returns_empty_list():
    from agent.infrastructure.tools.resolver import ToolResolver

    tools = await ToolResolver.resolve_all(None)

    assert tools == []


@pytest.mark.asyncio
async def test_given_disabled_config_when_resolve_all_called_then_skips_builder():
    from agent.infrastructure.tools.resolver import ToolResolver

    with patch("agent.infrastructure.tools.providers.mcp.MultiServerMCPClient") as MockClient:
        tools = await ToolResolver.resolve_all([
            {
                "type": "mcp",
                "enabled": False,
                "servers": {"server1": {"command": "test"}}
            }
        ])

        MockClient.assert_not_called()
        assert tools == []


@pytest.mark.asyncio
async def test_given_mcp_config_when_resolve_all_called_then_returns_tools():
    from agent.infrastructure.tools.resolver import ToolResolver

    mock_servers = {"server1": {"command": "test"}}
    mock_tools = ["tool1", "tool2"]

    with patch("agent.infrastructure.tools.providers.mcp.MultiServerMCPClient") as MockClient:
        instance = MockClient.return_value
        instance.get_tools = AsyncMock(return_value=mock_tools)

        tools = await ToolResolver.resolve_all([
            {
                "type": "mcp",
                "enabled": True,
                "servers": mock_servers
            }
        ])

        MockClient.assert_called_once_with(mock_servers)
        assert tools == mock_tools


@pytest.mark.asyncio
async def test_given_unknown_config_type_when_resolve_all_called_then_raises_value_error():
    from agent.infrastructure.tools.resolver import ToolResolver

    with pytest.raises(ValueError, match="Unknown tool type: unknown"):
        await ToolResolver.resolve_all([
            {
                "type": "unknown"
            }
        ])


def test_given_bootstrap_registration_when_agent_imported_then_mcp_is_registered():
    """Verify that the bootstrap registration in agent.agent registers MCP provider."""
    from agent.infrastructure.tools.resolver import ToolResolver
    # Importing agent triggers bootstrap registration
    import agent.core.agent  # noqa: F401
    
    # After bootstrap, mcp should be registered
    assert "mcp" in ToolResolver._REGISTRY
    assert callable(ToolResolver._REGISTRY["mcp"])


def test_given_mcp_provider_directly_imported_when_checking_registry_then_mcp_is_registered():
    """Verify that directly importing the MCP provider registers it in the ToolResolver."""
    from agent.infrastructure.tools.resolver import ToolResolver
    import agent.infrastructure.tools.providers.mcp  # noqa: F401
    
    assert "mcp" in ToolResolver._REGISTRY
    assert callable(ToolResolver._REGISTRY["mcp"])


@pytest.mark.asyncio
async def test_given_unregistered_tool_type_when_resolve_all_called_then_raises_descriptive_error():
    """Verify that using an unregistered tool type raises an error with the type name."""
    from agent.infrastructure.tools.resolver import ToolResolver
    
    unregistered_type = "nonexistent_tool_type"
    
    with pytest.raises(ValueError, match=f"Unknown tool type: {unregistered_type}"):
        await ToolResolver.resolve_all([
            {
                "type": unregistered_type,
                "enabled": True
            }
        ])
