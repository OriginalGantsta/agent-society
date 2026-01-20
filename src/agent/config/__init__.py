"""Configuration management for AI agents.

This package provides a simple architecture for loading agent configurations
from various sources.

Architecture:
    - AgentConfig: Core configuration model with factory methods
    - ConfigSource: Protocol for implementing configuration sources
    - FilesystemSource: Default filesystem-based implementation

Public API:
    - AgentConfig: The agent configuration model
    - ConfigSource: Protocol for implementing custom sources
    - FilesystemSource: Filesystem-based source (default)

Example:
    >>> from pathlib import Path
    >>> from agent.config import AgentConfig, FilesystemSource
    >>> 
    >>> # Load configuration
    >>> source = FilesystemSource(Path("./config"))
    >>> config_data = source.load(no_mcp=False)
    >>> config = AgentConfig.from_dict(config_data)
    >>> 
    >>> # Use the config
    >>> print(config.name, config.model_name)
"""
from .agent_config import AgentConfig
from .sources import ConfigSource, FilesystemSource

__all__ = ["AgentConfig", "ConfigSource", "FilesystemSource"]
