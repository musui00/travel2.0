"""
Agent 基类
所有自定义 Agent 应继承此类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from src.skills import get_all_tools


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str
    description: str = ""
    max_iterations: int = 10
    verbose: bool = True
    tools: Optional[List[Any]] = None


class BaseAgent(ABC):
    """
    Agent 基类
    定义 Agent 的通用接口
    """

    def __init__(self, llm: Any, config: Optional[AgentConfig] = None):
        self.llm = llm
        self.config = config or AgentConfig(name="base_agent")
        self.tools = self.config.tools or get_all_tools()

    @abstractmethod
    def run(self, input_text: str) -> str:
        """
        执行 Agent

        Args:
            input_text: 输入文本

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass

    def list_tools(self) -> List[str]:
        """列出可用的工具"""
        return [tool.name for tool in self.tools]

    def test(self) -> Dict[str, Any]:
        """测试 Agent 配置"""
        return {
            "status": "ok",
            "name": self.config.name,
            "description": self.config.description,
            "tools": self.list_tools(),
            "tool_count": len(self.tools),
        }
