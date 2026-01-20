"""Protocol defining the configuration source interface.

Any class implementing this protocol can provide configuration data,
enabling swappable backends (filesystem, database, HTTP API, etc.).
"""
from typing import Protocol, Any, Dict


class ConfigSource(Protocol):
    """Source of configuration data.
    
    This protocol defines the contract that all configuration sources
    must fulfill. Sources can be backed by any storage mechanism.
    
    The source is responsible for loading and assembling complete
    configuration data, including resolving tools (e.g., MCP injection).
    
    Examples:
        - Filesystem (JSON files)
        - Database (PostgreSQL, MongoDB)
        - HTTP API (remote config service)
        - In-memory (testing)
    """
    
    def load(self, no_mcp: bool = False) -> Dict[str, Any]:
        """Load complete agent configuration.
        
        Returns fully assembled configuration with all tools resolved.
        
        Args:
            no_mcp: Whether to prevent MCP tool injection
        
        Returns:
            Dictionary containing complete agent configuration
            
        Raises:
            FileNotFoundError: If required configuration is not found
            Exception: For other data source errors
        """
        ...
