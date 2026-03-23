"""
Sub-Agent 基类
定义子Agent的统一接口，用于处理特定领域的任务
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SubAgentConfig:
    """Sub-Agent 配置"""
    name: str
    description: str = ""
    max_tokens: int = 2000
    temperature: float = 0.7


class SubAgent(ABC):
    """
    Sub-Agent 基类
    负责特定领域的任务处理
    """

    def __init__(self, llm: Any, config: Optional[SubAgentConfig] = None):
        self.llm = llm
        self.config = config or SubAgentConfig(name="sub_agent")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """获取该领域可用的工具"""
        return []

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        执行子任务

        Args:
            task: 用户任务描述
            context: 上下文信息

        Returns:
            执行结果
        """
        context = context or {}

        # 构建提示词
        prompt = self._build_prompt(task, context)

        # 调用 LLM
        from langchain_core.messages import HumanMessage

        try:
            response = self.llm.invoke([
                HumanMessage(content=prompt)
            ])
            return response.content
        except Exception as e:
            return f"处理失败: {str(e)}"

    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """构建提示词"""
        prompt_parts = []

        # 添加上下文
        if context.get("image_analysis"):
            prompt_parts.append(f"图片分析结果：{context['image_analysis']}")

        if context.get("target_city"):
            prompt_parts.append(f"目标城市：{context['target_city']}")

        if context.get("budget"):
            prompt_parts.append(f"预算：{context['budget']}")

        if context.get("days"):
            prompt_parts.append(f"游玩天数：{context['days']}")

        prompt_parts.append(f"\n用户任务：{task}")

        return "\n\n".join(prompt_parts)

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "tools": [tool.name for tool in self.get_tools()],
        }
