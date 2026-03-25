"""
插件注册中心
单例模式管理所有插件的注册和获取
"""

import importlib
import inspect
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.plugin import Plugin


class PluginRegistry:
    """
    插件注册中心
    负责插件的注册、发现、加载和管理
    """

    _instance: Optional["PluginRegistry"] = None

    def __new__(cls) -> "PluginRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._plugins: Dict[str, Plugin] = {}
        self._tools_cache: Optional[List[Any]] = None
        self._initialized = True

    def register(self, plugin: Plugin) -> None:
        """注册插件"""
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"插件 {name} 已存在")
        self._plugins[name] = plugin
        # 清除缓存
        self._tools_cache = None

    def unregister(self, name: str) -> None:
        """注销插件"""
        if name in self._plugins:
            del self._plugins[name]
            self._tools_cache = None

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取插件"""
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """列出所有插件名称"""
        return list(self._plugins.keys())

    def get_all_tools(self) -> List[Any]:
        """获取所有插件的 Tools"""
        if self._tools_cache is not None:
            return self._tools_cache

        tools = []
        for plugin in self._plugins.values():
            tools.extend(plugin.get_tools())

        self._tools_cache = tools
        return tools

    def discover_skills(self, skills_dir: Optional[Path] = None) -> int:
        """
        自动发现并注册 Skills
        扫描 skills_dir 目录下的 *_skill.py 文件

        Returns:
            注册的技能数量
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent.parent / "skills"

        if not skills_dir.exists():
            return 0

        count = 0
        for file in skills_dir.glob("*_skill.py"):
            module_name = f"src.skills.{file.stem}"
            try:
                module = importlib.import_module(module_name)

                # 查找模块中的 Tool 对象（以 _tool 或 tool 结尾的函数/对象）
                for name, obj in inspect.getmembers(module):
                    if name.startswith("_") or name in ("TOOLS", "get_all_tools"):
                        continue
                    # 检查是否是有效的 Tool
                    if hasattr(obj, "name") and hasattr(obj, "invoke"):
                        from src.core.plugin import SkillPlugin

                        # 创建动态适配器
                        class AutoSkillPlugin(SkillPlugin):
                            def __init__(self, tool):
                                super().__init__(
                                    name=tool.name,
                                    description=tool.description or "",
                                )
                                self._tool = tool

                            def get_tools(self):
                                return [self._tool]

                            def test(self):
                                return {"status": "ok", "tool": self._tool.name}

                        self.register(AutoSkillPlugin(obj))
                        count += 1
            except Exception as e:
                print(f"加载模块 {module_name} 失败: {e}")

        return count

    def clear(self) -> None:
        """清除所有注册"""
        self._plugins.clear()
        self._tools_cache = None


def get_registry() -> PluginRegistry:
    """获取全局注册中心实例"""
    return PluginRegistry()
