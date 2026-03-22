"""
Skill 工具模块
封装外部 API 调用能力
使用 LangChain Tool 格式
支持动态加载和自动发现
"""

import os
import glob
from pathlib import Path
from typing import List, Any, Optional

# 导入所有 Skill
from src.skills.weather_skill import weather_query
from src.skills.flight_skill import flight_search
from src.skills.scenic_skill import scenic_ticket
from src.skills.recommend_skill import recommend_scenic
from src.skills.accommodation_skill import recommend_hotel, recommend_bnb
from src.skills.food_skill import recommend_restaurant, recommend_snacks
from src.skills.local_guide_skill import search_local_guide

# 导出所有工具
TOOLS = [
    weather_query,
    flight_search,
    scenic_ticket,
    recommend_scenic,
    recommend_hotel,
    recommend_bnb,
    recommend_restaurant,
    recommend_snacks,
    search_local_guide,
]


def get_all_tools() -> List[Any]:
    """
    获取所有 LangChain Tools
    自动从已注册的 Skills 中获取
    """
    return TOOLS


def get_tool(name: str) -> Optional[Any]:
    """
    根据名称获取指定的 Tool

    Args:
        name: Tool 名称

    Returns:
        Tool 对象，不存在返回 None
    """
    tool_map = {
        "weather_query": weather_query,
        "flight_search": flight_search,
        "scenic_ticket": scenic_ticket,
        "recommend_scenic": recommend_scenic,
        "recommend_hotel": recommend_hotel,
        "recommend_bnb": recommend_bnb,
        "recommend_restaurant": recommend_restaurant,
        "recommend_snacks": recommend_snacks,
        "search_local_guide": search_local_guide,
    }
    return tool_map.get(name)


def list_tool_names() -> List[str]:
    """列出所有可用的 Tool 名称"""
    return [tool.name for tool in TOOLS]


def test_tool(name: str, params: dict) -> Any:
    """
    测试指定的 Tool

    Args:
        name: Tool 名称
        params: 参数字典

    Returns:
        Tool 执行结果
    """
    tool = get_tool(name)
    if tool is None:
        raise ValueError(f"未知的 Tool: {name}")
    return tool.invoke(params)


__all__ = [
    "weather_query",
    "flight_search",
    "scenic_ticket",
    "recommend_scenic",
    "recommend_hotel",
    "recommend_bnb",
    "recommend_restaurant",
    "recommend_snacks",
    "search_local_guide",
    "TOOLS",
    "get_all_tools",
    "get_tool",
    "list_tool_names",
    "test_tool",
]
