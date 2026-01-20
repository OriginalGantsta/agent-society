"""Memory checkpointer provider."""
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver

from ..resolver import CheckpointerResolver


@CheckpointerResolver.register("memory")
def _build_memory_saver(_: Dict[str, Any]) -> Any:
    """Build a MemorySaver checkpointer instance."""
    return MemorySaver()
