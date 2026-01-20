"""Configuration sources package.

Provides the ConfigSource protocol and concrete implementations
for loading configuration from various backends.

Modules:
	- config_source: Defines the ConfigSource protocol
	- filesystem: Provides the default FilesystemSource implementation
"""
from .config_source import ConfigSource
from .filesystem import FilesystemSource

__all__ = ["ConfigSource", "FilesystemSource"]
