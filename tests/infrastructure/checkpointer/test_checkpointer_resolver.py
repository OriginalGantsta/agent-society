import pytest
from unittest.mock import MagicMock, patch


class TestCheckpointerResolver:
    """Tests for the CheckpointerResolver registry pattern."""

    @patch("agent.infrastructure.checkpointer.providers.memory.MemorySaver")
    def test_given_no_config_when_resolve_called_then_returns_memory_saver(self, mock_memory_saver):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver
        import agent.infrastructure.checkpointer.providers.memory

        mock_instance = MagicMock()
        mock_memory_saver.return_value = mock_instance

        checkpointer = CheckpointerResolver.resolve(None)

        mock_memory_saver.assert_called_once_with()
        assert checkpointer is mock_instance

    @patch("agent.infrastructure.checkpointer.providers.memory.MemorySaver")
    def test_given_memory_config_when_resolve_called_then_returns_memory_saver(self, mock_memory_saver):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver
        import agent.infrastructure.checkpointer.providers.memory

        mock_instance = MagicMock()
        mock_memory_saver.return_value = mock_instance

        config = {"type": "memory"}

        checkpointer = CheckpointerResolver.resolve(config)

        mock_memory_saver.assert_called_once_with()
        assert checkpointer is mock_instance

    @patch("agent.infrastructure.checkpointer.providers.sqlite.SqliteSaver")
    def test_given_sqlite_config_when_resolve_called_then_returns_sqlite_saver(self, mock_sqlite_saver):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver
        import agent.infrastructure.checkpointer.providers.sqlite

        mock_instance = MagicMock()
        mock_sqlite_saver.return_value = mock_instance

        config = {"type": "sqlite", "path": "./checkpoints.db"}

        checkpointer = CheckpointerResolver.resolve(config)

        mock_sqlite_saver.assert_called_once_with("./checkpoints.db")
        assert checkpointer is mock_instance

    @patch("agent.infrastructure.checkpointer.providers.postgres.PostgresSaver")
    def test_given_postgres_config_when_resolve_called_then_returns_postgres_saver(self, mock_postgres_saver):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver
        import agent.infrastructure.checkpointer.providers.postgres

        mock_instance = MagicMock()
        mock_postgres_saver.return_value = mock_instance

        config = {
            "type": "postgres",
            "connection_string": "postgresql://user:pass@localhost:5432/db"
        }

        checkpointer = CheckpointerResolver.resolve(config)

        mock_postgres_saver.assert_called_once_with(
            connection_string="postgresql://user:pass@localhost:5432/db"
        )
        assert checkpointer is mock_instance

    def test_given_unknown_type_when_resolve_called_then_raises_value_error(self):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver

        config = {"type": "unknown"}

        with pytest.raises(ValueError, match="Unknown checkpointer type: unknown"):
            CheckpointerResolver.resolve(config)

    def test_given_builder_function_when_register_decorator_called_then_adds_to_registry(self):
        from agent.infrastructure.checkpointer.resolver import CheckpointerResolver
        import agent.infrastructure.checkpointer.providers.memory
        import agent.infrastructure.checkpointer.providers.sqlite
        import agent.infrastructure.checkpointer.providers.postgres

        assert "memory" in CheckpointerResolver._REGISTRY
        assert "sqlite" in CheckpointerResolver._REGISTRY
        assert "postgres" in CheckpointerResolver._REGISTRY
        assert callable(CheckpointerResolver._REGISTRY["memory"])
