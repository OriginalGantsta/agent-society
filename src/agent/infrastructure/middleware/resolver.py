"""Middleware resolver infrastructure for building agent middleware."""
from typing import Any, Callable, Dict, List, Optional

from .specs import MiddlewareSpec


Builder = Callable[[Dict[str, Any]], Any]


class MiddlewareResolver:
    """Resolver for building agent middleware with registry extensibility."""

    _REGISTRY: Dict[str, Builder] = {}

    @classmethod
    def register(cls, middleware_type: str):
        """Decorator to register middleware builder functions."""

        def decorator(builder_func: Builder):
            cls._REGISTRY[middleware_type] = builder_func
            return builder_func

        return decorator

    @classmethod
    def resolve(cls, config: Dict[str, Any]) -> Optional[Any]:
        """Resolve a single middleware instance from configuration.
        
        Args:
            config: Dictionary containing middleware configuration with keys:
                - type: The middleware type (e.g., "summarization")
                - enabled: Whether the middleware is enabled (default: True)
                - other middleware-specific parameters
                
        Returns:
            Middleware instance or None if disabled
            
        Raises:
            ValueError: If the middleware type is not registered
        """
        if not config.get("enabled", True):
            return None

        middleware_type = config.get("type")

        if middleware_type not in cls._REGISTRY:
            raise ValueError(f"Unknown middleware type: {middleware_type}")

        builder = cls._REGISTRY[middleware_type]
        return builder(config)

    @classmethod
    def resolve_all(cls, configs: List[Dict[str, Any]]) -> List[Any]:
        """Resolve all middleware instances from a list of configurations.
        
        Args:
            configs: List of middleware configuration dictionaries
            
        Returns:
            List of middleware instances (excludes disabled middleware)
        """
        middleware = []
        for config in configs:
            mw = cls.resolve(config)
            if mw is not None:
                middleware.append(mw)
        return middleware
