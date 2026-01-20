"""Observability and tracing configuration.

Handles setup of external observability services like LangSmith.
"""
import os
import sys


def configure_langsmith(agent_name: str) -> None:
    """Configure LangSmith tracing environment variables.
    
    Sets up LangSmith tracing if LANGCHAIN_API_KEY is present in environment.
    This is a side effect that modifies environment variables.
    
    Args:
        agent_name: Name of the agent for project naming
    """
    if os.getenv("LANGCHAIN_API_KEY"):
        if not os.getenv("LANGCHAIN_TRACING_V2"):
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if not os.getenv("LANGCHAIN_PROJECT"):
            os.environ["LANGCHAIN_PROJECT"] = f"{agent_name}-project"
        print(f"LangSmith tracing enabled for project: {os.getenv('LANGCHAIN_PROJECT')}", file=sys.stderr)
    else:
        print("LangSmith tracing disabled. Set LANGCHAIN_API_KEY in .env to enable.", file=sys.stderr)
