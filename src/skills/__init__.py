"""
Skill工具模块
封装外部API调用能力
使用 LangChain Tool 格式
"""

from src.skills.weather_skill import weather_query
from src.skills.flight_skill import flight_search
from src.skills.scenic_skill import scenic_ticket

# 导出所有工具
TOOLS = [weather_query, flight_search, scenic_ticket]


def get_all_tools():
    """获取所有 LangChain Tools"""
    return TOOLS


__all__ = [
    "weather_query",
    "flight_search",
    "scenic_ticket",
    "TOOLS",
    "get_all_tools",
]
