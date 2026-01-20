import pytest
from typing import Dict, Any
from agent.config.agent_config import AgentConfig

@pytest.fixture
def valid_agent_config_dict() -> Dict[str, Any]:
    return {
        "name": "test-agent",
        "model": {
            "name": "gpt-4",
            "temperature": 0.5
        },
        "prompt": "Test system prompt",
        "tools": [
            {
                "type": "mcp",
                "enabled": True,
                "servers": {"server1": {"command": "test"}}
            }
        ],
        "checkpointer": {
            "type": "memory"
        }
    }

@pytest.fixture
def valid_agent_config(valid_agent_config_dict) -> AgentConfig:
    return AgentConfig.from_dict(valid_agent_config_dict)

