"""Agent package - Public API.

Exposes core Agent and AgentFactory classes for use by CLI, MCP server,
and other entrypoints.
"""
from agent.core import Agent, AgentFactory

__all__ = ["Agent", "AgentFactory"]
