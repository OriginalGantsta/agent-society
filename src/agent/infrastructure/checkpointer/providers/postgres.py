"""Postgres checkpointer provider."""
from typing import Any, Dict

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:  # pragma: no cover - optional dependency
    PostgresSaver = None  # type: ignore

from ..resolver import CheckpointerResolver


@CheckpointerResolver.register("postgres")
def _build_postgres_saver(config: Dict[str, Any]) -> Any:
    """Build a PostgresSaver checkpointer instance."""
    if PostgresSaver is None:
        raise ImportError("PostgresSaver is not available. Install langgraph with postgres extras.")

    connection_string = config.get("connection_string")
    if not connection_string:
        raise ValueError("Postgres checkpointer requires 'connection_string'")
    return PostgresSaver(connection_string=connection_string)
