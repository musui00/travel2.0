"""
Agent 工厂类
负责创建和管理 Agent 实例
"""

from typing import Any, Dict, Optional


class AgentFactory:
    """
    Agent 工厂类
    使用工厂模式创建不同类型的 Agent
    """

    _agents: Dict[str, type] = {}

    @classmethod
    def register(cls, agent_type: str, agent_class: type) -> None:
        """注册 Agent 类"""
        cls._agents[agent_type] = agent_class

    @classmethod
    def create(cls, agent_type: str, llm: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        """创建 Agent 实例"""
        if agent_type not in cls._agents:
            raise ValueError(f"未知的 Agent 类型: {agent_type}")

        agent_class = cls._agents[agent_type]
        return agent_class(llm, **(config or {}))

    @classmethod
    def list_agents(cls) -> list:
        """列出所有已注册的 Agent 类型"""
        return list(cls._agents.keys())


def register_default_agents():
    """注册默认的 Agent"""
    try:
        from src.agents.main_agent import MainAgent
        AgentFactory.register("main", MainAgent)
    except ImportError:
        pass


# 自动注册默认 Agent
register_default_agents()
