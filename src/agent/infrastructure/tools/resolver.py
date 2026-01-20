"""Tool resolver infrastructure for building agent tools."""
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .specs import ToolSpec


Builder = Callable[[Dict[str, Any]], Awaitable[List[Any]]]


class ToolResolver:
    """Resolver for building agent tools with registry extensibility."""

    _REGISTRY: Dict[str, Builder] = {}

    @classmethod
    def register(cls, tool_type: str):
        """Decorator to register tool builder functions."""

        def decorator(builder_func: Builder):
            cls._REGISTRY[tool_type] = builder_func
            return builder_func

        return decorator

    @classmethod
    async def resolve_all(cls, configs: Optional[List[ToolSpec]]) -> List[Any]:
        """Resolve all tool instances from configuration list."""
        if not configs:
            return []

        tools: List[Any] = []
        for config in configs:
            if not config.get("enabled", True):
                continue

            tool_type = config.get("type")
            if tool_type not in cls._REGISTRY:
                raise ValueError(f"Unknown tool type: {tool_type}")

            builder = cls._REGISTRY[tool_type]
            built_tools = await builder(config)
            if built_tools:
                tools.extend(built_tools)

        return tools
