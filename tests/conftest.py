"""
pytest fixtures
提供测试所需的共享 fixtures
"""

import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """设置测试环境变量"""
    # 确保使用测试环境
    os.environ["LOG_LEVEL"] = "ERROR"


@pytest.fixture
def mock_env():
    """模拟环境变量（测试前设置，测试后清理）"""
    original_env = os.environ.get("WEATHER_API_KEY")
    os.environ["WEATHER_API_KEY"] = "test_weather_key"
    yield
    if original_env is None:
        os.environ.pop("WEATHER_API_KEY", None)
    else:
        os.environ["WEATHER_API_KEY"] = original_env


@pytest.fixture
def clean_registry():
    """提供干净的注册中心（测试前清理，测试后恢复）"""
    from src.core.registry import get_registry

    registry = get_registry()
    registry.clear()
    yield registry
    registry.clear()


@pytest.fixture
def sample_llm():
    """模拟 LLM（用于测试）"""

    class MockLLM:
        def invoke(self, messages):
            class MockResponse:
                content = "Mock response"

            return MockResponse()

    return MockLLM()


@pytest.fixture
def weather_skill():
    """获取天气 Skill"""
    from src.skills.weather_skill import weather_query

    return weather_query


@pytest.fixture
def flight_skill():
    """获取航班 Skill"""
    from src.skills.flight_skill import flight_search

    return flight_skill


@pytest.fixture
def scenic_skill():
    """获取景点 Skill"""
    from src.skills.scenic_skill import scenic_ticket

    return scenic_ticket


@pytest.fixture
def all_tools():
    """获取所有 Tools"""
    from src.skills import get_all_tools

    return get_all_tools()
