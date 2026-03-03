"""
Skill工具模块
封装外部API调用能力
"""

from src.skills.base_skill import BaseSkill
from src.skills.weather_skill import WeatherSkill
from src.skills.flight_skill import FlightSkill
from src.skills.scenic_skill import ScenicSkill

# 注册所有可用技能
SKILLS = {
    "weather_query": WeatherSkill(),
    "flight_search": FlightSkill(),
    "scenic_ticket": ScenicSkill(),
}


def get_all_tools_schemas() -> list:
    """获取所有技能的工具schema（用于OpenAI Function Calling）"""
    return [skill.get_openai_schema() for skill in SKILLS.values()]


def execute_tool(tool_name: str, params: dict) -> str:
    """执行指定工具"""
    skill = SKILLS.get(tool_name)
    if skill:
        return skill.execute(params) or "工具执行失败"
    return f"未知的工具: {tool_name}"


__all__ = [
    "BaseSkill",
    "WeatherSkill",
    "FlightSkill",
    "ScenicSkill",
    "SKILLS",
    "get_all_tools_schemas",
    "execute_tool",
]
