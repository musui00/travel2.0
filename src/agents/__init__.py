"""
多智能体旅游规划系统
支持动态加载和自动发现
"""

from typing import Dict, Any, Optional, List

# 导入所有 Agent
from src.agents.main_agent import MainAgent

# Agent 注册表
_AGENTS: Dict[str, type] = {
    "main": MainAgent,
}


def register_agent(name: str, agent_class: type) -> None:
    """
    注册 Agent

    Args:
        name: Agent 名称
        agent_class: Agent 类
    """
    _AGENTS[name] = agent_class


def get_agent(name: str) -> Optional[type]:
    """
    获取 Agent 类

    Args:
        name: Agent 名称

    Returns:
        Agent 类，不存在返回 None
    """
    return _AGENTS.get(name)


def create_agent(name: str, llm: Any, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    创建 Agent 实例

    Args:
        name: Agent 名称
        llm: 语言模型实例
        config: 配置参数

    Returns:
        Agent 实例
    """
    agent_class = get_agent(name)
    if agent_class is None:
        raise ValueError(f"未知的 Agent: {name}")
    return agent_class(llm, **(config or {}))


def list_agents() -> List[str]:
    """列出所有可用的 Agent"""
    return list(_AGENTS.keys())


__all__ = [
    "MainAgent",
    "register_agent",
    "get_agent",
    "create_agent",
    "list_agents",
]
