"""Agent package CLI entrypoint.

Provides `main` and `parse_args` for tests and tooling.
"""
import argparse
import asyncio

from dotenv import load_dotenv

from agent.bootstrap import create_agent_from_args
from agent.cli.chat_handler import CLIChatHandler


async def main() -> None:
    """Main async entrypoint for the agent CLI."""
    load_dotenv()
    args = parse_args()

    try:
        agent = await create_agent_from_args(args)
        handler = CLIChatHandler(agent)

        await handler.start_session(query=args.query, thread_id=args.thread_id)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SimpleAgent - A ReAct agent with MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with default config
  python -m agent.cli.cli

  # Single query
  python -m agent.cli.cli "What is the weather today?"

  # Use custom config and MCP servers directory
  python -m agent.cli.cli --config my-config.json --mcp-dir ./my-servers --interactive

  # Continue a previous conversation
  python -m agent.cli.cli "Follow up question" --thread-id previous-session

  # Enable LangSmith tracing
  python -m agent.cli.cli --trace --interactive
        """,
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="Query to send to the agent (if not provided, runs in interactive mode)",
    )

    parser.add_argument(
        "--config",
        dest="config_base_path",
        type=str,
        default="config",
        help="Path to configuration directory (default: config)",
    )

    parser.add_argument(
        "--source-type",
        type=str,
        default="filesystem",
        choices=["filesystem", "postgres"],
        help="Configuration source type (default: filesystem)",
    )

    parser.add_argument(
        "--postgres-dsn",
        type=str,
        help="PostgreSQL connection string (required for postgres source)",
    )

    parser.add_argument(
        "--agent-name",
        type=str,
        help="Agent name to load from database (required for postgres source)",
    )

    parser.add_argument(
        "--mcp-dir",
        type=str,
        default="config/mcp_servers",
        help=(
            "Directory containing MCP server JSON files "
            "(deprecated, uses config dir)"
        ),
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode",
    )

    parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable LangSmith tracing",
    )

    parser.add_argument(
        "--thread-id",
        type=str,
        help="Thread ID for conversation continuity",
    )

    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Run without loading MCP servers",
    )

    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
