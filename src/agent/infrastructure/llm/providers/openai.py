"""OpenAI LLM provider."""
import os
from typing import Any, Dict

from langchain_openai import ChatOpenAI

from ..resolver import LLMResolver


@LLMResolver.register("openai")
def _build_openai_llm(config: Dict[str, Any]) -> Any:
    """Build a ChatOpenAI LLM instance."""
    # TODO: Instead of getting the API key from env, change to get from config
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Only OpenAI models are supported. Update the LLMResolver to support other models.")
    
    return ChatOpenAI(
        model=config.get("model_name"),
        temperature=config.get("temperature"),
        api_key=api_key,
        streaming=True
    )
