"""
Skill基类 - 所有工具的父类
定义工具的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSkill(ABC):
    """技能基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Optional[str]:
        """
        执行技能

        Args:
            params: 执行参数

        Returns:
            执行结果，失败返回None
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """
        获取技能Schema，用于LLM工具调用

        Returns:
            OpenAI工具格式的schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }
