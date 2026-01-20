"""Middleware configuration specs.

Declarative shapes for middleware resolver inputs.
"""
from typing import TypedDict


class MiddlewareSpec(TypedDict, total=False):
    """Specification for a middleware configuration."""

    type: str
    enabled: bool
