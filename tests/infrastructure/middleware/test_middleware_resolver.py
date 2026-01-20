import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch


class TestMiddlewareResolver:
    """Tests for the MiddlewareResolver registry pattern."""

    @patch('agent.infrastructure.middleware.providers.summarization.SummarizationMiddleware')
    def test_given_summarization_config_when_resolve_called_then_returns_summarization_middleware(self, mock_summarization):
        """Test creating SummarizationMiddleware from config dictionary."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver
        import agent.infrastructure.middleware.providers.summarization

        # Setup mock
        mock_instance = MagicMock()
        mock_instance.model = "gpt-4o-mini"
        mock_instance.trigger = ("tokens", 200)
        mock_instance.keep = ("messages", 1)
        mock_summarization.return_value = mock_instance

        config = {
            "type": "summarization",
            "enabled": True,
            "model": "gpt-4o-mini",
            "trigger": {
                "type": "tokens",
                "value": 200
            },
            "keep": {
                "type": "messages",
                "value": 1
            }
        }

        middleware = MiddlewareResolver.resolve(config)

        assert middleware is not None
        # Verify the middleware was created with correct parameters
        mock_summarization.assert_called_once_with(
            model="gpt-4o-mini",
            trigger=("tokens", 200),
            keep=("messages", 1)
        )
        assert middleware.model == "gpt-4o-mini"
        assert middleware.trigger == ("tokens", 200)
        assert middleware.keep == ("messages", 1)

    def test_given_disabled_middleware_when_resolve_called_then_returns_none(self):
        """Test that disabled middleware returns None."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver
        import agent.infrastructure.middleware.providers.summarization

        config = {
            "type": "summarization",
            "enabled": False,
            "model": "gpt-4o-mini",
            "trigger": {
                "type": "tokens",
                "value": 200
            },
            "keep": {
                "type": "messages",
                "value": 1
            }
        }

        middleware = MiddlewareResolver.resolve(config)

        assert middleware is None

    def test_given_unknown_type_when_resolve_called_then_raises_value_error(self):
        """Test that unknown middleware types raise ValueError."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver

        config = {
            "type": "unknown_middleware_type",
            "enabled": True
        }

        with pytest.raises(ValueError, match="Unknown middleware type: unknown_middleware_type"):
            MiddlewareResolver.resolve(config)

    @patch('agent.infrastructure.middleware.providers.summarization.SummarizationMiddleware')
    def test_given_multiple_configs_when_resolve_all_called_then_returns_all_enabled_middleware(self, mock_summarization):
        """Test creating multiple middleware instances from list of configs."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver
        import agent.infrastructure.middleware.providers.summarization

        # Setup mock
        mock_instance = MagicMock()
        mock_instance.model = "gpt-4o-mini"
        mock_summarization.return_value = mock_instance

        configs = [
            {
                "type": "summarization",
                "enabled": True,
                "model": "gpt-4o-mini",
                "trigger": {
                    "type": "tokens",
                    "value": 200
                },
                "keep": {
                    "type": "messages",
                    "value": 1
                }
            },
            {
                "type": "summarization",
                "enabled": False,
                "model": "gpt-4",
                "trigger": {
                    "type": "tokens",
                    "value": 500
                },
                "keep": {
                    "type": "messages",
                    "value": 5
                }
            }
        ]

        middleware_list = MiddlewareResolver.resolve_all(configs)

        # Only enabled middleware should be returned
        assert len(middleware_list) == 1
        # Verify only the enabled one was created
        mock_summarization.assert_called_once_with(
            model="gpt-4o-mini",
            trigger=("tokens", 200),
            keep=("messages", 1)
        )
        assert middleware_list[0].model == "gpt-4o-mini"

    def test_given_empty_configs_when_resolve_all_called_then_returns_empty_list(self):
        """Test that empty config list returns empty middleware list."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver

        middleware_list = MiddlewareResolver.resolve_all([])

        assert middleware_list == []

    @patch('agent.infrastructure.middleware.providers.summarization.SummarizationMiddleware')
    def test_given_config_without_enabled_field_when_resolve_called_then_defaults_to_enabled(self, mock_summarization):
        """Test that middleware without 'enabled' field defaults to enabled (True)."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver
        import agent.infrastructure.middleware.providers.summarization

        # Setup mock
        mock_instance = MagicMock()
        mock_summarization.return_value = mock_instance

        config = {
            "type": "summarization",
            "model": "gpt-4o-mini",
            "trigger": {
                "type": "tokens",
                "value": 200
            },
            "keep": {
                "type": "messages",
                "value": 1
            }
        }

        middleware = MiddlewareResolver.resolve(config)

        assert middleware is not None
        # Verify the middleware was created (defaults to enabled)
        mock_summarization.assert_called_once()

    def test_given_builder_function_when_register_decorator_called_then_adds_to_registry(self):
        """Test that the register decorator adds builders to the registry."""
        from agent.infrastructure.middleware.resolver import MiddlewareResolver
        import agent.infrastructure.middleware.providers.summarization

        # Verify summarization is registered
        assert "summarization" in MiddlewareResolver._REGISTRY
        assert callable(MiddlewareResolver._REGISTRY["summarization"])
