"""Agent runtime and composition.

Defines the interactive Agent and the AgentFactory responsible
for assembling it from configuration and infrastructure.
"""
from typing import AsyncGenerator

from langchain.agents import create_agent

from agent.config.agent_config import AgentConfig
from agent.infrastructure.llm.resolver import LLMResolver
from agent.infrastructure.middleware.resolver import MiddlewareResolver
from agent.infrastructure.tools.resolver import ToolResolver
from agent.infrastructure.checkpointer.resolver import CheckpointerResolver


def _register_providers() -> None:
	"""Register all infrastructure providers with their resolvers.
	
	These imports trigger decorator-based registration. They are not
	directly referenced but are required for the resolvers to function.
	"""
	# LLM providers
	import agent.infrastructure.llm.providers.openai  # noqa: F401
	
	# Middleware providers
	import agent.infrastructure.middleware.providers.summarization  # noqa: F401
	
	# Tool providers
	import agent.infrastructure.tools.providers.mcp  # noqa: F401
	
	# Checkpointer providers
	import agent.infrastructure.checkpointer.providers.memory  # noqa: F401
	import agent.infrastructure.checkpointer.providers.sqlite  # noqa: F401
	import agent.infrastructure.checkpointer.providers.postgres  # noqa: F401


# Bootstrap: Register all providers at module import time
_register_providers()


class Agent:
	"""Core agent runtime for LLM interactions."""

	def __init__(self, config: AgentConfig, graph):
		self.config = config
		self.graph = graph

	async def invoke(self, query: str, thread_id: str) -> str:
		"""Invoke the agent and return the complete response.
		
		This method is designed for programmatic use (e.g., MCP server)
		where you need the full response as a string rather than streaming.
		
		Args:
			query: User query/message
			thread_id: Thread identifier for conversation continuity
			
		Returns:
			Complete agent response as a string
		"""
		response_parts = []
		async for token in self.stream(query, thread_id):
			response_parts.append(token)
		return "".join(response_parts)

	async def stream(self, query: str, thread_id: str) -> AsyncGenerator[str, None]:
		"""Stream agent response tokens.
		
		Args:
			query: User query/message
			thread_id: Thread identifier for conversation continuity
			
		Yields:
			Response tokens as they are generated
		"""
		async for token, metadata in self.graph.astream(
			{"messages": [{"role": "user", "content": query}]},
			config={"configurable": {"thread_id": thread_id}},
			stream_mode="messages",
		):
			if self._is_not_summary_chunk(metadata):
				# Handle both string content and structured content (e.g., tool responses)
				content = token.content
				if isinstance(content, list):
					# Structured content from tool responses - extract text
					for item in content:
						if isinstance(item, dict) and item.get("type") == "text":
							yield item.get("text", "")
				elif isinstance(content, str):
					yield content

	def _is_not_summary_chunk(self, metadata: dict) -> bool:
		"""Check if a chunk is not from summarization middleware.
		
		Args:
			metadata: Chunk metadata
			
		Returns:
			True if chunk should be included in output
		"""
		is_summary_chunk = metadata.get("langgraph_node", "").startswith(
			"SummarizationMiddleware"
		)
		return not is_summary_chunk


class AgentFactory:
	"""Factory for creating and initializing Agent instances."""

	@staticmethod
	async def create(config: AgentConfig) -> Agent:
		"""Create and initialize an Agent instance from configuration."""
		tools = await ToolResolver.resolve_all(config.tool_configs)
		llm = LLMResolver.resolve(config.model_name, config.temperature)
		middleware = MiddlewareResolver.resolve_all(config.middleware_configs)
		checkpointer = CheckpointerResolver.resolve(config.checkpointer_config)

		graph = create_agent(
			model=llm,
			tools=tools,
			system_prompt=config.system_prompt,
			checkpointer=checkpointer,
			middleware=middleware,
		)

		return Agent(config, graph)


__all__ = ["Agent", "AgentFactory"]
