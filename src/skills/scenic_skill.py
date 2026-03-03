"""
景点门票查询Skill
查询景点门票价格、开放时间等信息
"""

from typing import Dict, Any, Optional
from src.skills.base_skill import BaseSkill


class ScenicSkill(BaseSkill):
    """景点门票查询技能"""

    def __init__(self):
        super().__init__(
            name="scenic_ticket",
            description="查询景点门票价格、开放时间、预约方式等信息",
        )

    def execute(self, params: Dict[str, Any]) -> Optional[str]:
        """
        查询景点门票

        Args:
            params: 包含 scenic_name, date 等字段

        Returns:
            门票信息字符串
        """
        scenic_name = params.get("scenic_name", "")
        date = params.get("date", "")

        if not scenic_name:
            return None

        # TODO: 接入真实景点门票API
        return self._mock_scenic(scenic_name, date)

    def _mock_scenic(self, scenic_name: str, date: str) -> str:
        """
        模拟景点查询

        Args:
            scenic_name: 景点名称
            date: 游玩日期

        Returns:
            景点信息
        """
        # 模拟数据
        return f"""
{scenic_name}景点信息：

- 门票价格：旺季 ¥60，淡季 ¥40
- 开放时间：08:00-18:00
- 建议游玩时长：3-4小时
- 预约方式：支持现场购票和线上预约
- 最佳游玩季节：春季、秋季
- 特色亮点：自然风光、历史文化

小贴士：
1. 建议提前在线预约，避免排队
2. 携带身份证入园
3. 景区内有多处餐饮点
"""

    def get_openai_schema(self) -> dict:
        """获取OpenAI工具调用格式的schema"""
        return {
            "type": "function",
            "function": {
                "name": "scenic_ticket",
                "description": "查询景点门票价格、开放时间、预约方式等信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenic_name": {
                            "type": "string",
                            "description": "景点名称，如：故宫、西湖、泰山",
                        },
                        "date": {"type": "string", "description": "游玩日期"},
                    },
                    "required": ["scenic_name"],
                },
            },
        }
