"""
单元测试 - 测试具体的 Skill 或函数
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSkills:
    """测试技能模块"""

    def test_weather_skill(self):
        """测试天气技能"""
        from src.skills.weather_skill import WeatherSkill

        skill = WeatherSkill()
        result = skill.execute({"city": "北京"})

        assert result is not None
        assert "北京" in result

    def test_weather_skill_schema(self):
        """测试天气技能Schema"""
        from src.skills.weather_skill import WeatherSkill

        skill = WeatherSkill()
        schema = skill.get_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "weather_query"
        assert "city" in schema["function"]["parameters"]["properties"]

    def test_flight_skill(self):
        """测试航班技能"""
        from src.skills.flight_skill import FlightSkill

        skill = FlightSkill()
        result = skill.execute({"from_city": "北京", "to_city": "上海"})

        assert result is not None
        assert "北京" in result
        assert "上海" in result

    def test_flight_skill_schema(self):
        """测试航班技能Schema"""
        from src.skills.flight_skill import FlightSkill

        skill = FlightSkill()
        schema = skill.get_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "flight_search"

    def test_scenic_skill(self):
        """测试景点门票技能"""
        from src.skills.scenic_skill import ScenicSkill

        skill = ScenicSkill()
        result = skill.execute({"scenic_name": "故宫"})

        assert result is not None
        assert "故宫" in result

    def test_scenic_skill_schema(self):
        """测试景点门票技能Schema"""
        from src.skills.scenic_skill import ScenicSkill

        skill = ScenicSkill()
        schema = skill.get_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "scenic_ticket"

    def test_get_all_tools_schemas(self):
        """测试获取所有工具Schema"""
        from src.skills import get_all_tools_schemas

        schemas = get_all_tools_schemas()
        assert len(schemas) == 3

        tool_names = [s["function"]["name"] for s in schemas]
        assert "weather_query" in tool_names
        assert "flight_search" in tool_names
        assert "scenic_ticket" in tool_names

    def test_execute_tool(self):
        """测试执行工具"""
        from src.skills import execute_tool

        result = execute_tool("weather_query", {"city": "杭州"})
        assert result is not None
        assert "杭州" in result


class TestPrompts:
    """测试Prompt模块"""

    def test_load_main_agent_prompts(self):
        """测试加载主Agent prompts"""
        from src.prompts import get_main_agent_prompts

        prompts = get_main_agent_prompts()
        assert "SYSTEM_PROMPT" in prompts
        assert "IMAGE_ANALYSIS_PROMPT" in prompts


class TestUtils:
    """测试工具模块"""

    def test_logger(self):
        """测试日志器"""
        from src.utils import logger

        # 测试日志方法存在
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
