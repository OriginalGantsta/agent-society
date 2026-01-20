"""Summarization middleware provider."""
from typing import Any, Dict

from langchain.agents.middleware import SummarizationMiddleware

from ..resolver import MiddlewareResolver


@MiddlewareResolver.register("summarization")
def _build_summarization(config: Dict[str, Any]):
    """Build a SummarizationMiddleware instance from config.
    
    Args:
        config: Configuration dictionary with keys:
            - model: Model name for summarization
            - trigger: Dict with 'type' and 'value' keys (e.g., {"type": "tokens", "value": 200})
            - keep: Dict with 'type' and 'value' keys (e.g., {"type": "messages", "value": 1})
    
    Returns:
        SummarizationMiddleware instance
    """
    trigger = config.get("trigger", {})
    keep = config.get("keep", {})

    return SummarizationMiddleware(
        model=config.get("model", "gpt-4o-mini"),
        trigger=(trigger.get("type"), trigger.get("value")),
        keep=(keep.get("type"), keep.get("value"))
    )
