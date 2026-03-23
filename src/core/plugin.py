"""
插件基类
定义插件的标准接口，所有 Skills 和 Agents 都继承此基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)


class Plugin(ABC):
    """插件基类"""

    metadata: PluginMetadata

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """获取插件提供的 LangChain Tools"""
        pass

    @abstractmethod
    def test(self) -> Dict[str, Any]:
        """运行插件自测，返回测试结果"""
        pass


class SkillPlugin(Plugin):
    """Skill 插件 - 继承此类创建新的 Skill"""

    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        self.metadata = PluginMetadata(
            name=name,
            version=version,
            description=description,
        )

    def get_tools(self) -> List[Any]:
        """子类必须实现，返回 LangChain Tool 列表"""
        raise NotImplementedError("子类必须实现 get_tools 方法")

    def test(self) -> Dict[str, Any]:
        """子类可覆盖，实现自测功能"""
        return {
            "status": "ok",
            "message": f"Plugin {self.metadata.name} loaded successfully",
        }


class AgentPlugin(Plugin):
    """Agent 插件 - 继承此类创建新的 Agent"""

    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        self.metadata = PluginMetadata(
            name=name,
            version=version,
            description=description,
        )

    def get_tools(self) -> List[Any]:
        """返回 Agent 使用的 Tools"""
        return []

    @abstractmethod
    def create_agent(self, llm: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        """创建 Agent 实例"""
        pass

    def test(self) -> Dict[str, Any]:
        """测试 Agent 配置"""
        return {
            "status": "ok",
            "message": f"Agent {self.metadata.name} loaded successfully",
        }
