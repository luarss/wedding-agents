"""
Agent Factory - Create agents with different configurations
"""

from dataclasses import dataclass, field
from typing import Any

from smolagents import CodeAgent, LiteLLMModel, Tool

from backend.config import config


@dataclass
class AgentConfig:
    """Configuration for creating an agent"""

    name: str
    description: str
    tools: list[str] = field(default_factory=list)  # Tool names from registry
    tool_instances: list[Tool] = field(default_factory=list)  # Or direct tool instances
    max_steps: int = 15
    verbosity_level: int = 2
    temperature: float = 0.7
    model_id: str | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)


class AgentFactory:
    """Factory for creating configured agents"""

    @staticmethod
    def create_agent(
        agent_config: AgentConfig,
        tool_registry: Any | None = None,  # ToolRegistry type
    ) -> CodeAgent:
        """Create an agent from configuration"""
        # Get tools
        tools = agent_config.tool_instances.copy()

        # Add tools from registry by name
        if agent_config.tools and tool_registry:
            tools.extend(tool_registry.create_instances(agent_config.tools))

        # Initialize model
        model = LiteLLMModel(
            model_id=agent_config.model_id or config.get_llm_model_id(),
            api_key=config.get_llm_api_key(),
            temperature=agent_config.temperature,
        )

        # Create agent
        return CodeAgent(
            tools=tools,
            model=model,
            max_steps=agent_config.max_steps,
            verbosity_level=agent_config.verbosity_level if config.AGENT_VERBOSE else 0,
            **agent_config.additional_params,
        )

    @staticmethod
    def create_from_dict(config_dict: dict[str, Any], tool_registry: Any | None = None) -> CodeAgent:
        """Create agent from dictionary configuration"""
        agent_config = AgentConfig(**config_dict)
        return AgentFactory.create_agent(agent_config, tool_registry)
