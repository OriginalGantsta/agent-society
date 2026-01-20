"""LLM resolver infrastructure for building language models."""
from typing import Any, Callable, Dict

from .specs import LLMSpec


Builder = Callable[[Dict[str, Any]], Any]


class LLMResolver:
    """Resolver for building language models with registry extensibility."""

    _REGISTRY: Dict[str, Builder] = {}

    @classmethod
    def register(cls, llm_type: str):
        """Decorator to register LLM builder functions."""

        def decorator(builder_func: Builder):
            cls._REGISTRY[llm_type] = builder_func
            return builder_func

        return decorator

    @classmethod
    def resolve(cls, model_name: str, temperature: float) -> Any:
        """Resolve an LLM instance from configuration.
        
        Args:
            model_name: Name of the model to use
            temperature: Temperature setting for the model
            
        Returns:
            LLM instance
            
        Note:
            This method uses a simplified API for backward compatibility.
            The type is automatically determined from available providers.
        """
        config = {
            "type": "openai",  # Default to OpenAI for now
            "model_name": model_name,
            "temperature": temperature
        }
        
        llm_type = config.get("type", "openai")
        
        if llm_type not in cls._REGISTRY:
            raise ValueError(f"Unknown LLM type: {llm_type}")
        
        builder = cls._REGISTRY[llm_type]
        return builder(config)
