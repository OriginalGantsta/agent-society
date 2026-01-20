"""Checkpointer configuration specs.

Declarative shapes for checkpointer resolver inputs.
"""
from typing import TypedDict


class CheckpointerSpec(TypedDict, total=False):
    """Specification for a checkpointer configuration."""

    type: str
