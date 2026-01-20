import pytest
from langchain_openai import ChatOpenAI
from agent.infrastructure.llm.resolver import LLMResolver
import agent.infrastructure.llm.providers.openai


def test_given_openai_key_when_resolve_llm_called_then_returns_chat_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    llm = LLMResolver.resolve("gpt-4", 0.5)

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4"
    assert llm.temperature == 0.5
    assert llm.openai_api_key.get_secret_value() == "test-key"


def test_given_no_api_key_when_resolve_llm_called_then_raises_value_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Only OpenAI models are supported"):
        LLMResolver.resolve("gpt-4", 0.5)


def test_given_builder_function_when_register_decorator_called_then_adds_to_registry():
    from agent.infrastructure.llm.resolver import LLMResolver

    assert "openai" in LLMResolver._REGISTRY
    assert callable(LLMResolver._REGISTRY["openai"])
