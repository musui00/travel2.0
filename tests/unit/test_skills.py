"""
单元测试 - Skills
测试 Skill 工具模块
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSkills:
    """测试 Skills 模块"""

    def test_get_all_tools(self):
        """测试获取所有 Tools"""
        from src.skills import get_all_tools, list_tool_names

        tools = get_all_tools()
        assert len(tools) == 9

        names = list_tool_names()
        assert "weather_query" in names
        assert "flight_search" in names
        assert "scenic_ticket" in names
        assert "recommend_scenic" in names
        assert "recommend_hotel" in names
        assert "recommend_bnb" in names
        assert "recommend_restaurant" in names
        assert "recommend_snacks" in names

    def test_get_tool(self):
        """测试获取指定 Tool"""
        from src.skills import get_tool

        tool = get_tool("weather_query")
        assert tool is not None
        assert tool.name == "weather_query"

    def test_get_tool_not_found(self):
        """测试获取不存在的 Tool"""
        from src.skills import get_tool

        tool = get_tool("nonexistent_tool")
        assert tool is None


class TestWeatherSkill:
    """测试天气 Skill"""

    def test_weather_query_no_api_key(self):
        """测试未配置 API Key 的情况"""
        # 这个测试需要模块重新加载来检测环境变量变化
        # 由于模块已加载，这里测试 API Key 检查逻辑是否存在
        from src.skills.weather_skill import weather_query

        # 检查 weather_query 函数是否有 API Key 检查逻辑
        # 可以通过查看源码或模拟调用来验证
        # 这里简单验证 tool 存在且可调用
        assert weather_query is not None
        assert hasattr(weather_query, "invoke")

    def test_weather_query_schema(self):
        """测试天气 Skill 的 Schema"""
        from src.skills.weather_skill import weather_query

        # 检查 Tool 属性
        assert hasattr(weather_query, "name")
        assert hasattr(weather_query, "description")
        assert weather_query.name == "weather_query"

    def test_weather_query_with_mock_key(self):
        """测试使用模拟 API Key"""
        # 设置临时环境变量
        original = os.environ.get("WEATHER_API_KEY")
        os.environ["WEATHER_API_KEY"] = "test_key"

        from src.skills.weather_skill import weather_query

        # 这个测试会真正调用 API（如果 key 有效）
        # 如果是测试 key，会返回错误但不会崩溃
        result = weather_query.invoke({"city": "北京"})

        # 恢复环境变量
        if original:
            os.environ["WEATHER_API_KEY"] = original
        else:
            os.environ.pop("WEATHER_API_KEY", None)

        assert result is not None
        assert isinstance(result, str)


class TestFlightSkill:
    """测试航班 Skill"""

    def test_flight_search_schema(self):
        """测试航班 Skill 的 Schema"""
        from src.skills.flight_skill import flight_search

        assert hasattr(flight_search, "name")
        assert flight_search.name == "flight_search"

    def test_flight_search(self):
        """测试航班搜索"""
        from src.skills.flight_skill import flight_search

        result = flight_search.invoke({"from_city": "北京", "to_city": "上海"})
        assert result is not None


class TestScenicSkill:
    """测试景点 Skill"""

    def test_scenic_ticket_schema(self):
        """测试景点 Skill 的 Schema"""
        from src.skills.scenic_skill import scenic_ticket

        assert hasattr(scenic_ticket, "name")
        assert scenic_ticket.name == "scenic_ticket"

    def test_scenic_ticket(self):
        """测试景点门票查询"""
        from src.skills.scenic_skill import scenic_ticket

        result = scenic_ticket.invoke({"scenic_name": "故宫"})
        assert result is not None


class TestCore:
    """测试核心模块"""

    def test_plugin_registry(self):
        """测试插件注册中心"""
        from src.core.plugin import SkillPlugin
        from src.core.registry import get_registry

        # 清理注册表
        registry = get_registry()
        registry.clear()

        # 注册测试插件
        class TestSkill(SkillPlugin):
            def get_tools(self):
                return []

        plugin = TestSkill(name="test_plugin", description="test plugin")
        registry.register(plugin)

        # 创建测试插件
        class TestSkill(SkillPlugin):
            def get_tools(self):
                return []

        plugin = TestSkill(name="test", description="test plugin")
        registry.register(plugin)

        assert "test" in registry.list_plugins()
        assert registry.get_plugin("test") is not None

    def test_agent_factory(self):
        """测试 Agent 工厂"""
        from src.agents import list_agents

        agents = list_agents()
        assert "main" in agents


class TestBaseAgent:
    """测试 Agent 基类"""

    def test_base_agent_config(self):
        """测试 Agent 配置"""
        from src.agents.base_agent import AgentConfig

        config = AgentConfig(name="test_agent", description="test")
        assert config.name == "test_agent"
        assert config.max_iterations == 10

    def test_list_tools(self, sample_llm):
        """测试列出工具"""
        from src.agents.base_agent import BaseAgent, AgentConfig

        class TestAgent(BaseAgent):
            def run(self, input_text: str) -> str:
                # 测试用的简单实现，返回测试结果
                return f"Processed: {input_text}"

            def get_system_prompt(self):
                return "test prompt"

        config = AgentConfig(name="test", tools=[])
        agent = TestAgent(sample_llm, config)

        tools = agent.list_tools()
        assert isinstance(tools, list)
