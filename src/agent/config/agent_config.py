"""Agent configuration model.

Defines AgentConfig, the core configuration data structure
for the agent application.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentConfig:
    """Configuration for an AI agent.

    Core data structure representing a fully configured agent.
    """

    name: str = "simple-agent"
    model_name: str = "gpt-4"
    temperature: float = 0
    system_prompt: str = "You are a helpful assistant."
    tool_configs: List[Dict[str, Any]] = field(default_factory=list)
    checkpointer_config: Optional[Dict[str, Any]] = None
    middleware_configs: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> "AgentConfig":
        """Construct AgentConfig from a configuration dictionary.
        
        Args:
            config_data: Complete configuration dictionary
            
        Returns:
            AgentConfig instance
        """
        agent_name = config_data.get("name", "simple-agent")
        model_data = config_data.get("model", {})
        model_name = model_data.get("name", "gpt-4")
        temperature = model_data.get("temperature", 0)
        system_prompt = config_data.get("prompt", "You are a helpful assistant.")
        tool_configs = config_data.get("tools", [])
        checkpointer_config = config_data.get("checkpointer")
        middleware_configs = config_data.get("middleware", [])

        return cls(
            name=agent_name,
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_prompt,
            tool_configs=tool_configs,
            checkpointer_config=checkpointer_config,
            middleware_configs=middleware_configs,
        )
