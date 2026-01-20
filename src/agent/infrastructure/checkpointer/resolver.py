"""Checkpointer resolver infrastructure for building agent checkpointers."""
from typing import Any, Callable, Dict, Optional

from .specs import CheckpointerSpec


Builder = Callable[[Dict[str, Any]], Any]


class CheckpointerResolver:
    """Resolver for building agent checkpointers with registry extensibility."""

    _REGISTRY: Dict[str, Builder] = {}

    @classmethod
    def register(cls, checkpointer_type: str):
        """Decorator to register checkpointer builder functions."""

        def decorator(builder_func: Builder):
            cls._REGISTRY[checkpointer_type] = builder_func
            return builder_func

        return decorator

    @classmethod
    def resolve(cls, config: Optional[CheckpointerSpec]) -> Any:
        """Resolve a checkpointer instance from configuration."""
        if config is None:
            config = {"type": "memory"}

        checkpointer_type = config.get("type", "memory")

        if checkpointer_type not in cls._REGISTRY:
            raise ValueError(f"Unknown checkpointer type: {checkpointer_type}")

        builder = cls._REGISTRY[checkpointer_type]
        return builder(config)
