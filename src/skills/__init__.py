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

__all__ = [
    "BaseSkill",
    "WeatherSkill",
    "FlightSkill",
    "ScenicSkill",
    "SKILLS"
]
