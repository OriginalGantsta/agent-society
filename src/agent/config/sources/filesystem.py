"""Filesystem-based configuration source.

Loads configuration from JSON files in a directory structure:
    config/
        agent.json          (required)
        mcp_servers.json    (optional)
"""
import json
from pathlib import Path
from typing import Any, Dict


class FilesystemSource:
    """Load configuration from filesystem JSON files.
    
    This is the default configuration source, reading from a directory
    containing agent.json and optionally mcp_servers.json.
    
    Handles MCP tool injection if no tools are explicitly defined.
    
    Args:
        base_path: Directory containing configuration files
        
    Example:
        >>> source = FilesystemSource(Path("./config"))
        >>> config_data = source.load(no_mcp=False)
    """
    
    def __init__(self, base_path: Path):
        """Initialize repository with base configuration directory.
        
        Args:
            base_path: Directory containing agent.json and optional mcp_servers.json
        """
        self.base_path = base_path
    
    def load(self, no_mcp: bool = False) -> Dict[str, Any]:
        """Load complete agent configuration with MCP tool injection if needed.
        
        Business Rules:
        1. If tools are explicitly defined in agent.json, use those
        2. If no tools defined and no_mcp=True, use no tools
        3. If no tools defined and MCP servers available, inject MCP tools
        4. Otherwise, use no tools
        
        Args:
            no_mcp: If True, prevent MCP tool injection
        
        Returns:
            Complete agent configuration dictionary with tools resolved
            
        Raises:
            FileNotFoundError: If base_path or agent.json doesn't exist
            json.JSONDecodeError: If JSON files are malformed
        """
        if not self.base_path.exists():
            raise FileNotFoundError(f"Config directory does not exist: {self.base_path}")
        
        agent_file = self.base_path / "agent.json"
        if not agent_file.exists():
            raise FileNotFoundError(f"Required agent config not found: {agent_file}")
        
        with open(agent_file) as f:
            agent_data = json.load(f)
        
        if "tools" in agent_data:
            return agent_data
        
        if no_mcp:
            print("Running without MCP servers (--no-mcp flag used)")
            return agent_data
        
        mcp_file = self.base_path / "mcp_servers.json"
        if not mcp_file.exists():
            print("No MCP servers config file found, proceeding without MCP tools.")
            return agent_data
        
        with open(mcp_file) as f:
            mcp_servers = json.load(f)
        
        agent_data["tools"] = [
            {
                "type": "mcp",
                "enabled": True,
                "servers": mcp_servers
            }
        ]
        
        return agent_data
