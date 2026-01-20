"""MCP tool builder for agent tools."""
from typing import Any, Dict, List

from langchain_mcp_adapters.client import MultiServerMCPClient

from ..resolver import ToolResolver


@ToolResolver.register("mcp")
async def _build_mcp_tools(config: Dict[str, Any]) -> List[Any]:
    """Build LangGraph tools from MCP servers."""
    servers = config.get("servers", {})
    if not servers:
        return []

    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()
    return tools
