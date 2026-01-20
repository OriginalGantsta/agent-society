"""Tool configuration specs.

Declarative shapes for tool resolver inputs.
"""
from typing import TypedDict


class ToolSpec(TypedDict, total=False):
    """Specification for a tool configuration."""

    type: str
    enabled: bool
