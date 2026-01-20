"""SQLite checkpointer provider."""
from typing import Any, Dict

try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except ImportError:  # pragma: no cover - optional dependency
    SqliteSaver = None  # type: ignore

from ..resolver import CheckpointerResolver


@CheckpointerResolver.register("sqlite")
def _build_sqlite_saver(config: Dict[str, Any]) -> Any:
    """Build a SqliteSaver checkpointer instance."""
    if SqliteSaver is None:
        raise ImportError("SqliteSaver is not available. Install langgraph with sqlite extras.")

    path = config.get("path")
    if not path:
        raise ValueError("Sqlite checkpointer requires 'path' to be set")
    return SqliteSaver(path)
