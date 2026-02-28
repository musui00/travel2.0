"""
测试模块
"""

import pytest
from unittest.mock import Mock, patch


class TestMainAgent:
    """测试主Agent"""

    def test_analyze_intent(self):
        """测试意图分析"""
        # TODO: 添加单元测试
        pass

    def test_execute_tasks(self):
        """测试任务执行"""
        # TODO: 添加单元测试
        pass


class TestSkills:
    """测试技能模块"""

    def test_weather_skill(self):
        """测试天气技能"""
        from src.skills.weather_skill import WeatherSkill

        skill = WeatherSkill()
        result = skill.execute({"city": "北京"})

        assert result is not None
        assert "北京" in result

    def test_flight_skill(self):
        """测试航班技能"""
        from src.skills.flight_skill import FlightSkill

        skill = FlightSkill()
        result = skill.execute({"from_city": "北京", "to_city": "上海"})

        assert result is not None
        assert "北京" in result
        assert "上海" in result

    def test_scenic_skill(self):
        """测试景点门票技能"""
        from src.skills.scenic_skill import ScenicSkill

        skill = ScenicSkill()
        result = skill.execute({"scenic_name": "故宫"})

        assert result is not None
        assert "故宫" in result
