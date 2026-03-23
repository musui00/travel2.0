"""
Core 模块
提供插件系统核心功能：插件基类、注册中心、工厂类
"""

from src.core.plugin import Plugin
from src.core.registry import PluginRegistry, get_registry
from src.core.factory import AgentFactory

__all__ = [
    "Plugin",
    "PluginRegistry",
    "get_registry",
    "AgentFactory",
]
