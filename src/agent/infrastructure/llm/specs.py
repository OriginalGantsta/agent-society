"""LLM configuration specs.

Declarative shapes for LLM resolver inputs.
"""
from typing import TypedDict


class LLMSpec(TypedDict, total=False):
    """Specification for an LLM configuration."""

    type: str
    model_name: str
    temperature: float
