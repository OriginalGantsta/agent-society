"""CLI chat session handler.

Handles interactive chat sessions and single-query execution for the CLI interface.
"""
import time
from typing import AsyncGenerator

from agent.cli.ui import CLIInterface


class CLIChatHandler:
    """Handles CLI-based chat sessions with the agent."""

    def __init__(self, agent):
        """Initialize the chat handler.
        
        Args:
            agent: Agent instance to handle chat requests
        """
        self.agent = agent

    async def start_session(self, query: str | None = None, thread_id: str | None = None) -> None:
        """Start a chat session with the agent.
        
        Args:
            query: Optional initial query. If provided, runs once and exits.
            thread_id: Optional thread ID for conversation continuity.
        """
        if not thread_id:
            thread_id = f"session-{int(time.time())}"

        CLIInterface.print_separator()
        CLIInterface.print_system(
            f"Started session with {self.agent.config.name} on thread ID: {thread_id}"
        )
        CLIInterface.print_system("Type 'exit' or 'quit' to end the conversation")
        CLIInterface.print_system("Type 'new' to start a new conversation thread")
        CLIInterface.print_separator()

        single_query_mode = query is not None

        while True:
            try:
                print()
                CLIInterface.print_user_prompt()
                if query:
                    user_input = query
                    query = None  # Clear query after first use
                    print(user_input)
                else:
                    user_input = CLIInterface.get_input()
                    print()

                if user_input.lower() in ["exit", "quit"]:
                    CLIInterface.print_system("Goodbye!")
                    break

                if user_input.lower() == "new":
                    thread_id = f"session-{int(time.time())}"
                    CLIInterface.print_system(
                        f"Started new session with {self.agent.config.name} on thread ID: {thread_id}"
                    )
                    continue

                if not user_input.strip():
                    continue

                CLIInterface.print_assistant_prefix()

                async for token in self.agent.stream(user_input, thread_id):
                    CLIInterface.print_chunk(token)

                if single_query_mode:
                    break

            except KeyboardInterrupt:
                CLIInterface.print_system("\n\nGoodbye!")
                break
            except Exception as e:  # noqa: BLE001
                CLIInterface.print_error(f"\nError: {e}")
