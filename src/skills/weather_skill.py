"""
天气查询Skill
调用外部天气API查询目的地天气
"""

import json
from typing import Dict, Any, Optional
from src.skills.base_skill import BaseSkill


class WeatherSkill(BaseSkill):
    """天气查询技能"""

    def __init__(self):
        super().__init__(
            name="weather_query",
            description="查询指定城市的天气情况，用于出行规划参考"
        )

    def execute(self, params: Dict[str, Any]) -> Optional[str]:
        """
        查询天气

        Args:
            params: 包含 city 字段

        Returns:
            天气信息字符串
        """
        city = params.get("city", "")

        if not city:
            return None

        # TODO: 这里可以接入真实的天气API
        # 例如：和风天气、天气API等
        # 示例使用占位数据
        return self._mock_weather(city)

    def _mock_weather(self, city: str) -> str:
        """
        模拟天气查询（实际使用时替换为真实API调用）

        Args:
            city: 城市名称

        Returns:
            天气信息
        """
        # 模拟返回数据
        weather_info = f"""
{city}今日天气：
- 天气：晴
- 温度：18-25°C
- 空气质量：优
- 出行建议：适合户外活动，请注意防晒
"""
        return weather_info

    def get_schema(self) -> Dict[str, Any]:
        """获取技能Schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "要查询的城市名称"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
