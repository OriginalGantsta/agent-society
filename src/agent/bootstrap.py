"""Agent bootstrap and initialization.

Provides shared agent creation logic for different entrypoints (CLI, MCP server, etc.).
"""
import argparse
from pathlib import Path

from agent.config import AgentConfig, FilesystemSource
from agent.config.sources.postgres import PostgresSource
from agent.observability import configure_langsmith
from agent.core import AgentFactory, Agent


async def create_agent_from_args(args: argparse.Namespace) -> Agent:
    """Create an agent instance from parsed CLI arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configured agent instance
        
    Raises:
        ValueError: If required arguments are missing or invalid
    """
    if args.source_type == "filesystem":
        source = FilesystemSource(Path(args.config_base_path))
    elif args.source_type == "postgres":
        if not args.postgres_dsn:
            raise ValueError("--postgres-dsn required when using postgres source")
        if not args.agent_name:
            raise ValueError("--agent-name required when using postgres source")
        source = PostgresSource(args.postgres_dsn, args.agent_name)
    else:
        raise ValueError(f"Unsupported source type: {args.source_type}")
    
    config_data = source.load(no_mcp=args.no_mcp)
    config = AgentConfig.from_dict(config_data)
    
    configure_langsmith(config.name)
    
    return await AgentFactory.create(config)
